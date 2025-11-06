#!/usr/bin/env python3

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Dict, Iterable, Optional, Tuple

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'fiqa_v1'))
DEFAULT_C10 = os.path.join(DATA_DIR, 'corpus_10k_v1.jsonl')
DEFAULT_C50 = os.path.join(DATA_DIR, 'corpus_50k_v1.jsonl')
DEFAULT_QRELS_10K = os.path.join(DATA_DIR, 'fiqa_qrels_10k_v1.jsonl')
DEFAULT_FIXED = os.path.join(DATA_DIR, 'corpus_10k_v1.fixed.jsonl')
DEFAULT_BAK = os.path.join(DATA_DIR, 'corpus_10k_v1.jsonl.bak')
DEFAULT_REPORT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'reports', 'fix_10k_docids.md'))

SPACE_RE = re.compile(r"\s+")
QUOTE_RE = re.compile(r"[\"\']+")


def normalize_text(text: str) -> str:
    if text is None:
        return ''
    t = text.lower().strip()
    t = QUOTE_RE.sub('', t)
    t = SPACE_RE.sub(' ', t).strip()
    return t


def sha1_hex(s: str) -> str:
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


@dataclass
class Record:
    doc_id: str
    title: str
    text: str

    @staticmethod
    def from_jsonl_line(line: str) -> 'Record':
        obj = json.loads(line)
        doc_id = str(obj.get('doc_id', '')).strip()
        title = obj.get('title', '') or ''
        text = obj.get('abstract') or obj.get('text') or ''
        return Record(doc_id=doc_id, title=title, text=text)

    def to_json(self) -> str:
        return json.dumps({
            'doc_id': self.doc_id,
            'title': self.title,
            'text': self.text,
        }, ensure_ascii=False)


def build_hash_map_50k(path_50k: str) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    h_full_to_id: Dict[str, str] = {}
    h_title_to_id: Dict[str, str] = {}
    h_text_to_id: Dict[str, str] = {}
    dup_full = 0
    with open(path_50k, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            r = Record.from_jsonl_line(line)
            full = normalize_text(f"{r.title} {r.text}")
            title_only = normalize_text(r.title)
            text_only = normalize_text(r.text)
            hf = sha1_hex(full)
            ht = sha1_hex(title_only)
            hx = sha1_hex(text_only)
            if hf in h_full_to_id and h_full_to_id[hf] != r.doc_id:
                dup_full += 1
            h_full_to_id[hf] = r.doc_id
            if title_only:
                h_title_to_id[ht] = r.doc_id
            if text_only:
                h_text_to_id[hx] = r.doc_id
    return h_full_to_id, h_title_to_id, h_text_to_id


def remap_record(
    rec: Record,
    h_full_to_id: Dict[str, str],
    h_title_to_id: Dict[str, str],
    h_text_to_id: Dict[str, str],
) -> Tuple[str, str]:
    full = normalize_text(f"{rec.title} {rec.text}")
    title_only = normalize_text(rec.title)
    text_only = normalize_text(rec.text)

    hf = sha1_hex(full)
    canonical = h_full_to_id.get(hf)
    if canonical is not None:
        return 'full', str(canonical)

    ht = sha1_hex(title_only) if title_only else None
    hx = sha1_hex(text_only) if text_only else None
    cand_t = h_title_to_id.get(ht) if ht else None
    cand_x = h_text_to_id.get(hx) if hx else None
    canonical = cand_t or cand_x
    if canonical is not None:
        return 'secondary', str(canonical)

    return 'unmatched', rec.doc_id


def compute_qrels_docids(path_qrels_10k: str) -> Tuple[int, int, int]:
    doc_ids = set()
    with open(path_qrels_10k, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            for d in obj.get('relevant_doc_ids', []):
                s = str(d)
                if s.isdigit():
                    doc_ids.add(int(s))
    if not doc_ids:
        return 0, 0, 0
    return len(doc_ids), min(doc_ids), max(doc_ids)


def write_report(report_path: str, stats: Dict[str, object]) -> None:
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        f.write('# FIQA 10k doc_id remap report\n\n')
        f.write('## Summary\n')
        f.write(f"- total_10k: {stats['total']}\n")
        f.write(f"- matched_full: {stats['matched_full']}\n")
        f.write(f"- matched_secondary: {stats['matched_secondary']}\n")
        f.write(f"- unmatched: {stats['unmatched']}\n")
        f.write(f"- match_rate: {stats['match_rate']:.4%}\n\n")
        f.write('## Ranges\n')
        f.write(f"- qrels_10k unique doc_ids: {stats['q_size']}, min={stats['q_min']}, max={stats['q_max']}\n")
        f.write(f"- corpus_10k doc_ids (before): {stats['c10_size_before']}, min={stats['c10_min_before']}, max={stats['c10_max_before']}\n")
        f.write(f"- corpus_10k doc_ids (after): {stats['c10_size_after']}, min={stats['c10_min_after']}, max={stats['c10_max_after']}\n")
        f.write(f"- corpus_50k doc_ids: {stats['c50_size']}, min={stats['c50_min']}, max={stats['c50_max']}\n\n")
        f.write('Acceptance: must be ≥ 99.5% matched.\n')


def load_docid_stats(path: str) -> Tuple[int, Optional[int], Optional[int]]:
    s = set()
    with open(path, 'r') as f:
        for line in f:
            if not line.strip():
                continue
            obj = json.loads(line)
            d = obj.get('doc_id')
            try:
                iv = int(d)
            except Exception:
                continue
            s.add(iv)
    if not s:
        return 0, None, None
    return len(s), min(s), max(s)


def main() -> int:
    parser = argparse.ArgumentParser(description='Remap FIQA 10k doc_ids to canonical space using content hashes from 50k corpus.')
    parser.add_argument('--c10', default=DEFAULT_C10, help='Path to 10k corpus jsonl')
    parser.add_argument('--c50', default=DEFAULT_C50, help='Path to 50k corpus jsonl')
    parser.add_argument('--qrels10k', default=DEFAULT_QRELS_10K, help='Path to qrels 10k jsonl')
    parser.add_argument('--out', default=DEFAULT_FIXED, help='Path to write fixed 10k corpus jsonl')
    parser.add_argument('--report', default=DEFAULT_REPORT, help='Path to write report markdown')
    parser.add_argument('--bak', default=DEFAULT_BAK, help='Backup of original 10k file')
    parser.add_argument('--min_match', type=float, default=0.995, help='Minimum acceptable match rate (0-1)')
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Pre-stats
    c10_size_before, c10_min_before, c10_max_before = load_docid_stats(args.c10)
    c50_size, c50_min, c50_max = load_docid_stats(args.c50)
    q_size, q_min, q_max = compute_qrels_docids(args.qrels10k)

    # Build maps
    h_full, h_title, h_text = build_hash_map_50k(args.c50)

    # Remap and write (single pass streaming + counting)
    total = 0
    matched_full = 0
    matched_secondary = 0
    unmatched = 0

    if not os.path.exists(args.bak) and os.path.exists(args.c10):
        try:
            import shutil
            shutil.copy2(args.c10, args.bak)
        except Exception as e:
            print(f"[warn] failed to create backup: {e}", file=sys.stderr)

    with open(args.c10, 'r') as in_f, open(args.out, 'w') as out_f:
        for line in in_f:
            line = line.strip()
            if not line:
                continue
            total += 1
            rec = Record.from_jsonl_line(line)
            kind, new_id = remap_record(rec, h_full, h_title, h_text)
            if kind == 'full':
                matched_full += 1
            elif kind == 'secondary':
                matched_secondary += 1
            else:
                unmatched += 1
            rec.doc_id = new_id
            out_f.write(rec.to_json() + '\n')

    # Post-stats on fixed
    c10_size_after, c10_min_after, c10_max_after = load_docid_stats(args.out)

    match_rate = (matched_full + matched_secondary) / total if total else 0.0

    stats = {
        'total': total,
        'matched_full': matched_full,
        'matched_secondary': matched_secondary,
        'unmatched': unmatched,
        'match_rate': match_rate,
        'q_size': q_size,
        'q_min': q_min,
        'q_max': q_max,
        'c10_size_before': c10_size_before,
        'c10_min_before': c10_min_before,
        'c10_max_before': c10_max_before,
        'c10_size_after': c10_size_after,
        'c10_min_after': c10_min_after,
        'c10_max_after': c10_max_after,
        'c50_size': c50_size,
        'c50_min': c50_min,
        'c50_max': c50_max,
    }

    write_report(args.report, stats)

    print(json.dumps(stats, indent=2))

    if match_rate < args.min_match:
        print(f"Match rate {match_rate:.4%} below threshold {args.min_match:.3%}", file=sys.stderr)
        return 2

    return 0


if __name__ == '__main__':
    sys.exit(main())
