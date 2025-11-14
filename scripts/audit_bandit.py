#!/usr/bin/env python3
"""
Bandit/Grid strategy audit script.

Scans the repository for bandit-related components and produces structured
reports under the `.runs` directory to support reuse vs. rebuild decisions.
"""
from __future__ import annotations

import ast
import json
import logging
import os
import re
import subprocess
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]
RUNS_DIR = ROOT / ".runs"
LOG_FILE = RUNS_DIR / "bandit_audit.log"

KEYWORD_PATTERN = re.compile(
    r"(bandit|epsilon|eps_greedy|ucb|thompson|multiarmed|arm|arms|grid|selector|strategy)",
    re.IGNORECASE,
)

SYMBOL_PATTERNS: List[re.Pattern[str]] = [
    re.compile(r"eps", re.IGNORECASE),
    re.compile(r"greedy", re.IGNORECASE),
    re.compile(r"ucb", re.IGNORECASE),
    re.compile(r"thompson", re.IGNORECASE),
    re.compile(r"bandit", re.IGNORECASE),
    re.compile(r"grid", re.IGNORECASE),
    re.compile(r"select", re.IGNORECASE),
    re.compile(r"arm", re.IGNORECASE),
    re.compile(r"strategy", re.IGNORECASE),
    re.compile(r"tuner", re.IGNORECASE),
    re.compile(r"ab", re.IGNORECASE),
]

TRACE_TOKENS = [
    "retrieval_proxy_client",
    "X-Trace-Id",
    "trace_url",
]

EXTERNAL_DEP_HINTS = {"requests", "numpy", "pandas", "scipy", "sklearn", "torch"}

SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".idea",
    ".vscode",
    "node_modules",
    ".gitlab",
}


def setup_logging() -> None:
    RUNS_DIR.mkdir(exist_ok=True)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.info("Bandit audit started at root %s", ROOT)


def iter_repository_files() -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(ROOT, topdown=True):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES and not d.startswith(".git")]
        for filename in filenames:
            yield Path(dirpath) / filename


def read_text_safely(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="latin-1")
        except Exception:
            logging.exception("Failed to read %s", path)
            return ""
    except Exception:
        logging.exception("Failed to read %s", path)
        return ""


def find_keyword_hits() -> Dict[str, str]:
    hits: Dict[str, str] = {}
    for path in iter_repository_files():
        try:
            if not path.is_file():
                continue
            text = read_text_safely(path)
            if not text:
                continue
            if KEYWORD_PATTERN.search(path.name) or KEYWORD_PATTERN.search(text):
                rel = str(path.relative_to(ROOT))
                hits[rel] = text
        except Exception:
            logging.exception("Error scanning %s", path)
    logging.info("Detected %d candidate files with keyword hits", len(hits))
    return hits


def filter_symbols(names: Iterable[str]) -> List[str]:
    matched: List[str] = []
    for name in names:
        for pattern in SYMBOL_PATTERNS:
            if pattern.search(name):
                matched.append(name)
                break
    return sorted(set(matched))


def extract_io_from_function(node: ast.FunctionDef) -> Dict[str, object]:
    args = []
    defaults = [None] * (len(node.args.args) - len(node.args.defaults)) + list(node.args.defaults)
    for arg, default in zip(node.args.args, defaults):
        default_repr = ast.unparse(default) if default is not None else None
        args.append({"name": arg.arg, "default": default_repr})
    if node.args.vararg:
        args.append({"name": f"*{node.args.vararg.arg}", "default": None})
    if node.args.kwarg:
        args.append({"name": f"**{node.args.kwarg.arg}", "default": None})
    returns = ast.unparse(node.returns) if node.returns is not None else None
    return {"name": node.name, "args": args, "returns": returns}


def analyse_python_file(path: Path, source: str) -> Dict[str, object]:
    info: Dict[str, object] = {
        "path": str(path),
        "symbols": {"classes": [], "functions": []},
        "entrypoints": {"has_main": False, "has_argparse": False},
        "dependencies": {"imports": [], "external": []},
        "io": [],
        "reuse_tag": "rewrite",
        "notes": [],
    }
    try:
        tree = ast.parse(source)
    except SyntaxError:
        logging.exception("AST parse failed for %s", path)
        info["notes"].append("ast_parse_failed")
        return info

    class_names = []
    function_names = []
    io_contracts = []
    imports: List[str] = []
    external: List[str] = []
    has_main = False
    has_argparse = False

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            class_names.append(node.name)
        elif isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
            if SYMBOL_PATTERNS[6].search(node.name) or SYMBOL_PATTERNS[7].search(node.name):
                io_contracts.append(extract_io_from_function(node))
        elif isinstance(node, ast.If):
            if (
                isinstance(node.test, ast.Compare)
                and len(node.test.ops) == 1
                and isinstance(node.test.ops[0], ast.Eq)
            ):
                left = node.test.left
                comparators = node.test.comparators
                if isinstance(left, ast.Name) and left.id == "__name__":
                    if comparators and isinstance(comparators[0], (ast.Constant, ast.Str)):
                        compare_value = (
                            comparators[0].value if isinstance(comparators[0], ast.Constant) else comparators[0].s
                        )
                        if compare_value == "__main__":
                            has_main = True
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            imports.append(module)

    matched_classes = filter_symbols(class_names)
    matched_functions = filter_symbols(function_names)

    if "argparse" in imports:
        has_argparse = True
    external = sorted({name.split(".")[0] for name in imports if name.split(".")[0] in EXTERNAL_DEP_HINTS})

    info["symbols"]["classes"] = matched_classes
    info["symbols"]["functions"] = matched_functions
    info["entrypoints"]["has_main"] = has_main
    info["entrypoints"]["has_argparse"] = has_argparse
    info["dependencies"]["imports"] = sorted(set(imports))
    info["dependencies"]["external"] = external
    info["io"] = io_contracts

    text_lower = source.lower()
    reuse_signals = any(token.lower() in text_lower for token in TRACE_TOKENS)
    structured = bool(matched_classes or matched_functions or has_main or has_argparse)
    if reuse_signals:
        info["reuse_tag"] = "reuse"
    elif structured:
        info["reuse_tag"] = "adapt"
    else:
        info["reuse_tag"] = "rewrite"
    return info


def scan_makefile(makefile_path: Path) -> List[Dict[str, object]]:
    targets: List[Dict[str, object]] = []
    if not makefile_path.exists():
        logging.info("Makefile not found at %s", makefile_path)
        return targets
    text = read_text_safely(makefile_path)
    lines = text.splitlines()
    target_pattern = re.compile(r"^([A-Za-z0-9_.-]+):")
    pending_target: Optional[str] = None
    buffer: List[str] = []

    for line in lines:
        match = target_pattern.match(line)
        if match:
            if pending_target is not None:
                if KEYWORD_PATTERN.search(pending_target) or any(KEYWORD_PATTERN.search(cmd) for cmd in buffer):
                    targets.append({"target": pending_target, "commands": buffer.copy()})
            pending_target = match.group(1)
            buffer = []
        else:
            if pending_target is not None and line.startswith("\t"):
                buffer.append(line.strip())

    if pending_target is not None:
        if KEYWORD_PATTERN.search(pending_target) or any(KEYWORD_PATTERN.search(cmd) for cmd in buffer):
            targets.append({"target": pending_target, "commands": buffer.copy()})

    filtered = [
        t for t in targets if re.search(r"(bandit|grid|tuner|ab)", t["target"], re.IGNORECASE)
        or any(re.search(r"(bandit|grid|tuner|ab)", cmd, re.IGNORECASE) for cmd in t["commands"])
    ]
    logging.info("Collected %d Make targets matching audit filters", len(filtered))
    return filtered


def scan_readmes(root: Path) -> Dict[str, List[str]]:
    readme_hits: Dict[str, List[str]] = {}
    for path in root.rglob("README*.md"):
        text = read_text_safely(path)
        if not text:
            continue
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        matches = [p for p in paragraphs if KEYWORD_PATTERN.search(p)]
        if matches:
            readme_hits[str(path.relative_to(ROOT))] = matches
    logging.info("Located %d README files with relevant sections", len(readme_hits))
    return readme_hits


def derive_role(path: str, symbols: Dict[str, List[str]]) -> str:
    low = path.lower()
    candidates = symbols["classes"] + symbols["functions"]
    text = " ".join(candidates).lower()
    if "selector" in low or "selector" in text:
        return "selector"
    if "tuner" in low or "tuner" in text:
        return "tuner"
    if "strategy" in low or "strategy" in text:
        return "strategy"
    if "grid" in low or "grid" in text:
        return "grid-search"
    if "bandit" in low or "bandit" in text:
        return "bandit"
    if "ab" in low or "ab" in text:
        return "ab-test"
    return "component"


def compose_map_markdown(file_reports: List[Dict[str, object]]) -> str:
    lines = [
        "| 模块 | 角色 | 输入 | 输出 | 依赖 | 复用建议 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for report in file_reports:
        module = report["path"]
        role = derive_role(module, report["symbols"])
        inputs = ", ".join(arg["name"] for io in report["io"] for arg in io.get("args", [])) or "-"
        outputs = ", ".join(io.get("returns") or "-" for io in report["io"]) or "-"
        deps = ", ".join(report["dependencies"]["external"] or report["dependencies"]["imports"][:5]) or "-"
        reuse = report["reuse_tag"]
        lines.append(f"| `{module}` | {role} | {inputs} | {outputs} | {deps} | {reuse} |")
    return "\n".join(lines)


def compose_todo_markdown(file_reports: List[Dict[str, object]], readme_hits: Dict[str, List[str]]) -> str:
    reuse_count = sum(1 for r in file_reports if r["reuse_tag"] == "reuse")
    adapt_count = sum(1 for r in file_reports if r["reuse_tag"] == "adapt")
    rewrite_count = sum(1 for r in file_reports if r["reuse_tag"] == "rewrite")

    suggestions = [
        "- P0: 接入 `retrieval_proxy_client` 或统一代理层，打通 trace 与调用链。",
        "- P0: 为策略输出补齐 `.runs` 级别的 JSON 契约，便于下游重放与回归。",
        "- P1: 添加 `X-Trace-Id`/`trace_url` 透传，支持链路追踪与复盘。",
    ]

    if adapt_count == 0 and reuse_count == 0:
        suggestions.append("- P1: 评估重建 `modules/autotune/selector.py`，补齐缺失策略封装。")
    if readme_hits:
        suggestions.append("- P1: 将 README 策略说明同步至代码注释，避免知识漂移。")
    if rewrite_count:
        suggestions.append("- P0: 清理或替换依赖缺失/废弃模块，保障可执行路径。")

    summary = [
        f"- 统计：reuse={reuse_count}, adapt={adapt_count}, rewrite={rewrite_count}",
        "- 建议：",
    ] + suggestions
    return "\n".join(summary)


def collect_smoke_commands(file_reports: List[Dict[str, object]]) -> List[str]:
    commands: List[str] = []
    for report in file_reports:
        entry = report["entrypoints"]
        if entry.get("has_main") or entry.get("has_argparse"):
            module_path = Path(report["path"])
            if module_path.suffix == ".py":
                rel = module_path.relative_to(ROOT)
                commands.append(f"python {rel}")
    return commands


def write_json(path: Path, data: object) -> None:
    try:
        with path.open("w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
    except Exception:
        logging.exception("Failed to write JSON to %s", path)


def write_text(path: Path, content: str) -> None:
    try:
        with path.open("w", encoding="utf-8") as handle:
            handle.write(content.strip() + "\n")
    except Exception:
        logging.exception("Failed to write text to %s", path)


def main() -> None:
    setup_logging()
    try:
        hits = find_keyword_hits()
        file_reports: List[Dict[str, object]] = []

        for rel_path, text in hits.items():
            path = ROOT / rel_path
            if path.suffix == ".py":
                report = analyse_python_file(path, text)
                file_reports.append(report)

        readme_hits = scan_readmes(ROOT)
        make_targets = scan_makefile(ROOT / "Makefile")

        if not file_reports:
            logging.info("No Python files matched keyword filters; audit outputs will be empty placeholders.")

        # Outputs
        write_json(RUNS_DIR / "bandit_audit.json", {"files": file_reports, "readmes": readme_hits})
        write_text(RUNS_DIR / "bandit_map.md", compose_map_markdown(file_reports) if file_reports else "| 模块 | 角色 | 输入 | 输出 | 依赖 | 复用建议 |\n| --- | --- | --- | --- | --- | --- |\n")
        write_text(
            RUNS_DIR / "bandit_targets.txt",
            "\n".join(
                f"{target['target']}:\n  " + "\n  ".join(target["commands"]) if target["commands"] else f"{target['target']}:"
                for target in make_targets
            )
            if make_targets
            else "",
        )
        write_text(RUNS_DIR / "bandit_todo.md", compose_todo_markdown(file_reports, readme_hits))

        smoke_commands = collect_smoke_commands(file_reports)
        if smoke_commands:
            write_text(
                RUNS_DIR / "bandit_smoke_plan.txt",
                "\n".join(f"# Plan for {cmd.split()[1] if len(cmd.split()) > 1 else cmd}\n{cmd} --dry-run" for cmd in smoke_commands),
            )

        logging.info("Audit completed. Reports written to %s", RUNS_DIR)
    except Exception:
        logging.exception("Unexpected failure in audit script")


if __name__ == "__main__":
    main()

