#!/usr/bin/env python3
"""
Auto Insurance RAG Evaluation Script
=====================================
Evaluates retrieval quality using hit@k and relevance heuristics.

Usage:
    python scripts/eval_auto_insurance_rag.py [--collection auto_insurance_v2_clean]
"""

import os
import sys
import json
import time
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import defaultdict
from urllib.parse import urlparse

# Load environment variables
try:
    from dotenv import load_dotenv
    from pathlib import Path
    load_dotenv()
    env_cloudrun = Path('.env.cloudrun')
    if env_cloudrun.exists():
        load_dotenv(env_cloudrun, override=True)
except ImportError:
    pass

try:
    from fastembed import TextEmbedding
    FASTEMBED_AVAILABLE = True
except ImportError:
    FASTEMBED_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

from qdrant_client import QdrantClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Model configuration (must match embed_and_upsert.py)
MODEL_NAME = "BAAI/bge-m3"
FALLBACK_MODEL = "mixedbread-ai/mxbai-embed-large-v1"

# Authoritative domains (get boost in relevance)
AUTHORITATIVE_DOMAINS = {"dmv.ca.gov", "insurance.ca.gov"}


class EmbeddingGenerator:
    """Embedding generator matching embed_and_upsert.py"""
    
    def __init__(self):
        logger.info(f"Initializing embedding model: {MODEL_NAME}")
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                logger.info(f"Using sentence-transformers for {MODEL_NAME}")
                self.model = SentenceTransformer(MODEL_NAME)
                self.use_fastembed = False
                self.actual_model = MODEL_NAME
                logger.info(f"✅ Embedding model loaded: {MODEL_NAME}")
                return
            except Exception as e:
                logger.warning(f"sentence-transformers failed: {e}, trying fastembed fallback...")
        
        if FASTEMBED_AVAILABLE:
            try:
                logger.info(f"Trying fastembed for {MODEL_NAME}")
                self.model = TextEmbedding(model_name=MODEL_NAME)
                self.use_fastembed = True
                self.actual_model = MODEL_NAME
                logger.info(f"✅ Embedding model loaded: {MODEL_NAME}")
                return
            except Exception as e:
                logger.warning(f"fastembed doesn't support {MODEL_NAME}: {e}")
                try:
                    logger.info(f"Using fallback model: {FALLBACK_MODEL}")
                    self.model = TextEmbedding(model_name=FALLBACK_MODEL)
                    self.use_fastembed = True
                    self.actual_model = FALLBACK_MODEL
                    logger.warning(f"⚠️ Using fallback model {FALLBACK_MODEL}")
                    return
                except Exception as e2:
                    logger.error(f"Fallback model also failed: {e2}")
        
        raise RuntimeError(f"Failed to load model {MODEL_NAME}")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings"""
        try:
            if self.use_fastembed:
                embeddings = list(self.model.embed(texts))
            else:
                embeddings = self.model.encode(texts, convert_to_numpy=True).tolist()
            return embeddings
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise


class RelevanceChecker:
    """Check if a result is relevant to a query"""
    
    def __init__(self):
        # Define keyword sets for each question type (multi-language)
        self.keyword_sets = {
            "minimum_requirements": {
                "en": ["minimum", "requirement", "required", "coverage", "liability", "15/30/5", "15-30-5", "california"],
                "zh": ["最低", "要求", "必须", "保险", "责任", "加州", "california"],
                "es": ["mínimo", "requisito", "requerido", "cobertura", "responsabilidad", "california"]
            },
            "liability_limits": {
                "en": ["liability", "limit", "bodily injury", "property damage", "15/30/5", "coverage amount"],
                "zh": ["责任", "限额", "人身伤害", "财产损失", "保额"],
                "es": ["responsabilidad", "límite", "lesiones corporales", "daños a la propiedad"]
            },
            "sr22": {
                "en": ["sr-22", "sr22", "certificate", "financial responsibility", "filing", "required"],
                "zh": ["sr-22", "sr22", "证书", "财务责任", "文件", "需要"],
                "es": ["sr-22", "sr22", "certificado", "responsabilidad financiera", "presentar", "requerido"]
            },
            "proof_insurance": {
                "en": ["proof", "insurance", "card", "certificate", "show", "provide", "evidence"],
                "zh": ["证明", "保险", "卡", "证书", "显示", "提供"],
                "es": ["prueba", "seguro", "tarjeta", "certificado", "mostrar", "proporcionar"]
            },
            "claims": {
                "en": ["claim", "file", "report", "accident", "damage", "process", "step"],
                "zh": ["理赔", "申请", "报告", "事故", "损坏", "流程", "步骤"],
                "es": ["reclamo", "presentar", "reportar", "accidente", "daño", "proceso", "paso"]
            },
            "coverage_types": {
                "en": ["coverage", "type", "comprehensive", "collision", "liability", "uninsured", "motorist"],
                "zh": ["保险", "类型", "全险", "碰撞", "责任", "未投保", "驾驶人"],
                "es": ["cobertura", "tipo", "completo", "colisión", "responsabilidad", "sin seguro", "conductor"]
            },
            "uninsured_motorist": {
                "en": ["uninsured", "motorist", "underinsured", "um", "uim", "coverage"],
                "zh": ["未投保", "驾驶人", "不足额", "保险"],
                "es": ["sin seguro", "conductor", "subasegurado", "cobertura"]
            },
            "medical_payments": {
                "en": ["medical", "payment", "pip", "personal injury", "protection", "med pay"],
                "zh": ["医疗", "支付", "人身伤害", "保护"],
                "es": ["médico", "pago", "lesiones personales", "protección"]
            },
            "comprehensive_collision": {
                "en": ["comprehensive", "collision", "deductible", "coverage", "repair"],
                "zh": ["全险", "碰撞", "免赔额", "保险", "维修"],
                "es": ["completo", "colisión", "deducible", "cobertura", "reparación"]
            },
            "discounts": {
                "en": ["discount", "save", "saving", "reduction", "lower", "rate", "premium"],
                "zh": ["折扣", "节省", "减少", "降低", "费率", "保费"],
                "es": ["descuento", "ahorrar", "reducción", "bajar", "tasa", "prima"]
            },
            "policy_changes": {
                "en": ["policy", "change", "update", "modify", "add", "remove", "driver", "vehicle"],
                "zh": ["保单", "更改", "更新", "修改", "添加", "删除", "驾驶员", "车辆"],
                "es": ["póliza", "cambiar", "actualizar", "modificar", "agregar", "eliminar", "conductor", "vehículo"]
            },
            "cancellation": {
                "en": ["cancel", "cancellation", "terminate", "end", "policy", "coverage"],
                "zh": ["取消", "终止", "结束", "保单", "保险"],
                "es": ["cancelar", "cancelación", "terminar", "finalizar", "póliza", "cobertura"]
            },
            "nonrenewal": {
                "en": ["nonrenewal", "non-renewal", "renew", "renewal", "not renew"],
                "zh": ["不续保", "续保", "更新"],
                "es": ["no renovación", "renovar", "renovación"]
            },
            "rate_factors": {
                "en": ["rate", "factor", "premium", "cost", "price", "affect", "determine", "calculate"],
                "zh": ["费率", "因素", "保费", "成本", "价格", "影响", "确定", "计算"],
                "es": ["tasa", "factor", "prima", "costo", "precio", "afectar", "determinar", "calcular"]
            },
            "adding_drivers": {
                "en": ["add", "driver", "policy", "coverage", "include", "additional"],
                "zh": ["添加", "驾驶员", "保单", "保险", "包括", "额外"],
                "es": ["agregar", "conductor", "póliza", "cobertura", "incluir", "adicional"]
            },
            "accident_forgiveness": {
                "en": ["accident", "forgiveness", "forgive", "waive", "protect", "rate"],
                "zh": ["事故", "宽恕", "免除", "保护", "费率"],
                "es": ["accidente", "perdón", "perdonar", "eximir", "proteger", "tasa"]
            }
        }
    
    def is_relevant(self, query_type: str, result: Dict, query_text: str, query_used: Optional[str] = None, eval_mode: str = "normal") -> Tuple[bool, List[str]]:
        """
        Check if result is relevant using keyword matching and domain authority.
        
        Returns: (is_relevant, matched_keywords)
        """
        title = result.get("title", "").lower()
        text = result.get("text", "").lower()
        url = result.get("source_url", "").lower()
        result_lang = result.get("language", "en").lower()
        
        # For translated mode, use the English query for keyword matching
        if eval_mode == "translated" and query_used:
            query_for_matching = query_used.lower()
            query_lang = "en"  # Always use English keywords for translated queries
        else:
            query_for_matching = query_text.lower()
            # Detect query language (simple heuristic)
            query_lang = "en"
            if any('\u4e00' <= c <= '\u9fff' for c in query_text):
                query_lang = "zh"
            elif any(c in "áéíóúñü¿" for c in query_text.lower()):
                query_lang = "es"
        
        # Get keyword set for query type and language
        keyword_dict = self.keyword_sets.get(query_type, {})
        if isinstance(keyword_dict, dict):
            # Multi-language format - use English keywords for translated queries
            keyword_set = keyword_dict.get("en", []) if eval_mode == "translated" else keyword_dict.get(query_lang, keyword_dict.get("en", []))
        else:
            # Legacy format (list)
            keyword_set = keyword_dict if isinstance(keyword_dict, list) else []
        
        matched_keywords = []
        
        # Check domain authority (prioritize authoritative domains)
        parsed = urlparse(url)
        domain = parsed.netloc.lower().replace('www.', '')
        is_authoritative = domain in AUTHORITATIVE_DOMAINS
        
        # Check keyword matches
        if keyword_set:
            for kw in keyword_set:
                kw_lower = kw.lower()
                if kw_lower in title or kw_lower in text:
                    matched_keywords.append(kw)
        
        # For translated mode: prioritize authoritative domains + keyword matches
        if eval_mode == "translated":
            if is_authoritative:
                # Authoritative domain: need at least 1 keyword match
                return (len(matched_keywords) >= 1, matched_keywords)
            else:
                # Non-authoritative: need at least 2 keyword matches
                return (len(matched_keywords) >= 2, matched_keywords)
        
        # Normal mode: original logic
        if is_authoritative:
            if keyword_set:
                return (len(matched_keywords) >= 1, matched_keywords)
            return (True, matched_keywords)  # Trust authoritative domain
        
        # For non-authoritative domains, need at least 2 keyword matches
        if keyword_set:
            return (len(matched_keywords) >= 2, matched_keywords)
        
        # Fallback: check if query words appear (for unknown types)
        query_words = set(query_for_matching.split())
        text_words = set((title + " " + text).split())
        common = query_words.intersection(text_words)
        matched_keywords = list(common)
        return (len(common) >= 2, matched_keywords)


class RAGEvaluator:
    """RAG evaluation suite"""
    
    def __init__(self, collection_name: str, qdrant_url: str, qdrant_api_key: Optional[str]):
        self.collection_name = collection_name
        self.embedder = EmbeddingGenerator()
        self.relevance_checker = RelevanceChecker()
        
        logger.info(f"Connecting to Qdrant Cloud: {qdrant_url}")
        client_kwargs = {"url": qdrant_url}
        if qdrant_api_key:
            client_kwargs["api_key"] = qdrant_api_key
        self.client = QdrantClient(**client_kwargs)
        
        # Verify collection exists
        try:
            info = self.client.get_collection(collection_name)
            logger.info(f"✅ Collection {collection_name} found: {info.points_count} points")
        except Exception as e:
            logger.error(f"Collection {collection_name} not found: {e}")
            raise
    
    def get_evaluation_queries(self) -> List[Dict]:
        """Get evaluation query set"""
        return [
            # English queries (8)
            {
                "query": "What are the minimum auto insurance requirements in California?",
                "type": "minimum_requirements",
                "language": "en"
            },
            {
                "query": "How to file an auto insurance claim?",
                "type": "claims",
                "language": "en"
            },
            {
                "query": "What is SR-22 and when is it required?",
                "type": "sr22",
                "language": "en"
            },
            {
                "query": "What are the liability limits for auto insurance?",
                "type": "liability_limits",
                "language": "en"
            },
            {
                "query": "What is uninsured motorist coverage?",
                "type": "uninsured_motorist",
                "language": "en"
            },
            {
                "query": "What is comprehensive and collision coverage?",
                "type": "comprehensive_collision",
                "language": "en"
            },
            {
                "query": "What discounts are available for auto insurance?",
                "type": "discounts",
                "language": "en"
            },
            {
                "query": "How to add a driver to my auto insurance policy?",
                "type": "adding_drivers",
                "language": "en"
            },
            # Chinese queries (8)
            {
                "query": "加州最低汽车保险要求是什么？",
                "type": "minimum_requirements",
                "language": "zh"
            },
            {
                "query": "如何申请汽车保险理赔？",
                "type": "claims",
                "language": "zh"
            },
            {
                "query": "SR-22 是什么，什么时候需要？",
                "type": "sr22",
                "language": "zh"
            },
            {
                "query": "汽车保险的责任限额是多少？",
                "type": "liability_limits",
                "language": "zh"
            },
            {
                "query": "什么是未投保驾驶人保险？",
                "type": "uninsured_motorist",
                "language": "zh"
            },
            {
                "query": "什么是全险和碰撞险？",
                "type": "comprehensive_collision",
                "language": "zh"
            },
            {
                "query": "汽车保险有哪些折扣？",
                "type": "discounts",
                "language": "zh"
            },
            {
                "query": "如何在我的汽车保险单中添加驾驶员？",
                "type": "adding_drivers",
                "language": "zh"
            },
            # Spanish queries (4)
            {
                "query": "¿Cuáles son los requisitos mínimos de seguro de auto en California?",
                "type": "minimum_requirements",
                "language": "es"
            },
            {
                "query": "¿Cómo presentar un reclamo de seguro de auto?",
                "type": "claims",
                "language": "es"
            },
            {
                "query": "¿Qué es SR-22 y cuándo se requiere?",
                "type": "sr22",
                "language": "es"
            },
            {
                "query": "¿Qué es la cobertura de conductor sin seguro?",
                "type": "uninsured_motorist",
                "language": "es"
            },
            # Additional business queries (4)
            {
                "query": "What proof of insurance do I need to show?",
                "type": "proof_insurance",
                "language": "en"
            },
            {
                "query": "How to cancel my auto insurance policy?",
                "type": "cancellation",
                "language": "en"
            },
            {
                "query": "What factors affect my auto insurance rate?",
                "type": "rate_factors",
                "language": "en"
            },
            {
                "query": "What is accident forgiveness coverage?",
                "type": "accident_forgiveness",
                "language": "en"
            }
        ]
    
    def evaluate_query(self, query_info: Dict, top_k: int = 5, translate_zh: bool = False, eval_mode: str = "normal") -> Dict:
        """Evaluate a single query"""
        query_text = query_info["query"]
        query_type = query_info["type"]
        language = query_info["language"]
        
        # Translation support: translate Chinese queries to English for search
        query_used = query_text
        translation_applied = False
        if translate_zh and language == "zh":
            try:
                # Add project root to path for import
                import sys
                import os
                from pathlib import Path
                project_root = Path(__file__).parent.parent.resolve()
                if str(project_root) not in sys.path:
                    sys.path.insert(0, str(project_root))
                
                # Temporarily enable translation for evaluation
                original_enabled = os.getenv("TRANSLATION_ENABLED", "0")
                os.environ["TRANSLATION_ENABLED"] = "1"
                os.environ["TRANSLATION_PROVIDER"] = os.getenv("TRANSLATION_PROVIDER", "argos")
                
                from services.fiqa_api.utils.translation import translate_zh_to_en, is_translation_available
                
                # Check if translation is available
                if is_translation_available():
                    translated = translate_zh_to_en(query_text)
                    if translated and translated.strip() and translated != query_text:
                        query_used = translated
                        translation_applied = True
                        logger.info(f"[eval] Translated query: {query_text[:50]}... -> {translated[:50]}...")
                    else:
                        logger.warning(f"[eval] Translation returned empty or same as original")
                else:
                    logger.warning(f"[eval] Translation service not available (install argostranslate)")
                
                # Restore original env
                os.environ["TRANSLATION_ENABLED"] = original_enabled
            except Exception as e:
                logger.warning(f"[eval] Translation failed for query: {e}")
                # Fallback: use original query
        
        start_time = time.time()
        
        try:
            # Generate query embedding (use translated query if available)
            query_embedding = self.embedder.embed([query_used])[0]
            
            # Search Qdrant
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True
            )
            
            # Format results
            formatted_results = []
            for r in results:
                payload = r.payload or {}
                formatted_results.append({
                    "id": str(r.id),
                    "score": float(r.score) if hasattr(r, 'score') else 0.0,
                    "title": payload.get("title", "Unknown"),
                    "text": payload.get("text", "")[:300],
                    "source_url": payload.get("source_url", ""),
                    "language": payload.get("language", "en")
                })
            
            # Check relevance
            relevant_count = 0
            result_details = []
            for result in formatted_results:
                is_rel, matched_kw = self.relevance_checker.is_relevant(
                    query_type, result, query_text, 
                    query_used=query_used if translation_applied else None,
                    eval_mode=eval_mode
                )
                if is_rel:
                    relevant_count += 1
                result_details.append({
                    "title": result.get("title", ""),
                    "source_url": result.get("source_url", ""),
                    "score": result.get("score", 0.0),
                    "relevant": is_rel,
                    "matched_keywords": matched_kw
                })
            
            # Get top domain
            top_domain = None
            if formatted_results:
                parsed = urlparse(formatted_results[0].get("source_url", ""))
                top_domain = parsed.netloc.lower().replace('www.', '')
            
            latency_ms = (time.time() - start_time) * 1000
            best_score = formatted_results[0]["score"] if formatted_results else 0.0
            
            return {
                "query": query_text,
                "query_used": query_used,  # Query actually used for search
                "translation_applied": translation_applied,
                "type": query_type,
                "language": language,
                "best_score": best_score,
                "relevant_count_in_top5": relevant_count,
                "top1_domain": top_domain,
                "latency_ms": latency_ms,
                "results": formatted_results,
                "result_details": result_details,  # Detailed results with relevance info
                "hit@5": relevant_count / top_k if top_k > 0 else 0.0
            }
        except Exception as e:
            logger.error(f"Failed to evaluate query '{query_text}': {e}")
            return {
                "query": query_text,
                "query_used": query_used,
                "translation_applied": translation_applied,
                "type": query_type,
                "language": language,
                "error": str(e),
                "best_score": 0.0,
                "relevant_count_in_top5": 0,
                "top1_domain": None,
                "latency_ms": 0.0,
                "results": [],
                "result_details": [],
                "hit@5": 0.0
            }
    
    def run_evaluation(self, translate_zh: bool = False, eval_mode: str = "normal") -> Dict:
        """
        Run full evaluation suite
        
        Args:
            translate_zh: Whether to translate Chinese queries to English for search
            eval_mode: "normal" (use original query for relevance) or "translated" (use translated query for relevance)
        """
        logger.info("=" * 60)
        logger.info("Starting RAG Evaluation")
        if translate_zh:
            logger.info("Translation mode: ENABLED (Chinese queries will be translated to English)")
        logger.info(f"Evaluation mode: {eval_mode}")
        logger.info("=" * 60)
        
        queries = self.get_evaluation_queries()
        logger.info(f"Evaluating {len(queries)} queries...")
        
        results = []
        for idx, query_info in enumerate(queries, 1):
            logger.info(f"[{idx}/{len(queries)}] Evaluating: {query_info['query'][:60]}...")
            result = self.evaluate_query(query_info, translate_zh=translate_zh, eval_mode=eval_mode)
            results.append(result)
            
            # Log result
            logger.info(f"  Hit@5: {result['hit@5']:.2f}, Relevant: {result['relevant_count_in_top5']}/5, "
                       f"Top domain: {result['top1_domain']}, Latency: {result['latency_ms']:.1f}ms")
        
        # Compute aggregate metrics
        total_queries = len(results)
        total_hit = sum(r["hit@5"] for r in results)
        avg_hit_at_5 = total_hit / total_queries if total_queries > 0 else 0.0
        
        queries_with_3_plus = sum(1 for r in results if r["relevant_count_in_top5"] >= 3)
        pct_queries_3_plus = (queries_with_3_plus / total_queries * 100) if total_queries > 0 else 0.0
        
        total_latency = sum(r["latency_ms"] for r in results)
        avg_latency = total_latency / total_queries if total_queries > 0 else 0.0
        
        # Language breakdown
        lang_stats = defaultdict(lambda: {"count": 0, "avg_hit": 0.0, "total_hit": 0.0})
        for r in results:
            lang = r["language"]
            lang_stats[lang]["count"] += 1
            lang_stats[lang]["total_hit"] += r["hit@5"]
        for lang in lang_stats:
            lang_stats[lang]["avg_hit"] = lang_stats[lang]["total_hit"] / lang_stats[lang]["count"]
        
        # Find worst queries
        worst_queries = sorted(results, key=lambda x: x["hit@5"])[:5]
        
        summary = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "collection": self.collection_name,
            "total_queries": total_queries,
            "avg_hit_at_5": avg_hit_at_5,
            "pct_queries_with_3_plus_relevant": pct_queries_3_plus,
            "avg_latency_ms": avg_latency,
            "language_breakdown": dict(lang_stats),
            "queries": results,
            "worst_queries": [
                {
                    "query": q["query"],
                    "type": q["type"],
                    "hit@5": q["hit@5"],
                    "relevant_count": q["relevant_count_in_top5"],
                    "top_domain": q["top1_domain"]
                }
                for q in worst_queries
            ]
        }
        
        # Check acceptance criteria
        passed = avg_hit_at_5 >= 0.6 and pct_queries_3_plus >= 70.0
        summary["passed"] = passed
        
        logger.info("=" * 60)
        logger.info("EVALUATION SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Average Hit@5: {avg_hit_at_5:.3f}")
        logger.info(f"Queries with >=3 relevant: {queries_with_3_plus}/{total_queries} ({pct_queries_3_plus:.1f}%)")
        logger.info(f"Average Latency: {avg_latency:.1f}ms")
        logger.info(f"\nLanguage Breakdown:")
        for lang, stats in lang_stats.items():
            logger.info(f"  {lang}: {stats['count']} queries, avg hit@5: {stats['avg_hit']:.3f}")
        
        if passed:
            logger.info("\n✅ EVALUATION PASSED")
        else:
            logger.info("\n❌ EVALUATION FAILED")
            logger.info(f"  Target: avg_hit@5 >= 0.6, >=70% queries with 3+ relevant")
            logger.info(f"  Actual: avg_hit@5 = {avg_hit_at_5:.3f}, {pct_queries_3_plus:.1f}% with 3+ relevant")
            logger.info(f"\nWorst 5 queries:")
            for q in worst_queries:
                logger.info(f"  - {q['query'][:60]}: hit@5={q['hit@5']:.2f}, relevant={q['relevant_count_in_top5']}/5")
        
        return summary


def generate_reports(summary: Dict, report_dir: Path, report_name: str = "EVAL_REPORT"):
    """Generate markdown and JSON reports"""
    report_dir.mkdir(parents=True, exist_ok=True)
    
    # JSON report
    json_path = report_dir / f"{report_name}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    logger.info(f"✅ JSON report saved to {json_path}")
    
    # Markdown report
    md_path = report_dir / f"{report_name}.md"
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Auto Insurance RAG Evaluation Report\n\n")
        f.write(f"**Generated**: {summary['timestamp']}\n\n")
        f.write(f"**Collection**: `{summary['collection']}`\n\n")
        f.write(f"## Summary Metrics\n\n")
        f.write(f"- **Total Queries**: {summary['total_queries']}\n")
        f.write(f"- **Average Hit@5**: {summary['avg_hit_at_5']:.3f}\n")
        f.write(f"- **Queries with >=3 Relevant**: {summary['pct_queries_with_3_plus_relevant']:.1f}%\n")
        f.write(f"- **Average Latency**: {summary['avg_latency_ms']:.1f}ms\n")
        f.write(f"- **Status**: {'✅ PASSED' if summary['passed'] else '❌ FAILED'}\n\n")
        
        f.write(f"## Language Breakdown\n\n")
        for lang, stats in summary['language_breakdown'].items():
            f.write(f"- **{lang}**: {stats['count']} queries, avg hit@5: {stats['avg_hit']:.3f}\n")
        f.write("\n")
        
        f.write(f"## Per-Query Results\n\n")
        for q in summary['queries']:
            f.write(f"### {q['query']}\n\n")
            f.write(f"- **Type**: {q['type']}\n")
            f.write(f"- **Language**: {q['language']}\n")
            if q.get('query_used') and q.get('query_used') != q['query']:
                f.write(f"- **Query Used (Translated)**: {q['query_used']}\n")
            f.write(f"- **Translation Applied**: {q.get('translation_applied', False)}\n")
            f.write(f"- **Hit@5**: {q['hit@5']:.3f}\n")
            f.write(f"- **Relevant in Top5**: {q['relevant_count_in_top5']}/5\n")
            f.write(f"- **Best Score**: {q['best_score']:.4f}\n")
            f.write(f"- **Top Domain**: {q['top1_domain']}\n")
            f.write(f"- **Latency**: {q['latency_ms']:.1f}ms\n\n")
            
            # Top 5 results with details
            if q.get('result_details'):
                f.write(f"#### Top 5 Results:\n\n")
                for idx, res in enumerate(q['result_details'][:5], 1):
                    f.write(f"{idx}. **{res['title']}**\n")
                    f.write(f"   - URL: {res['source_url']}\n")
                    f.write(f"   - Score: {res['score']:.4f}\n")
                    f.write(f"   - Relevant: {'✅' if res['relevant'] else '❌'}\n")
                    if res.get('matched_keywords'):
                        f.write(f"   - Matched Keywords: {', '.join(res['matched_keywords'])}\n")
                    f.write("\n")
            
            if q.get('error'):
                f.write(f"- **Error**: {q['error']}\n\n")
        
        if not summary['passed']:
            f.write(f"## Worst Performing Queries\n\n")
            for q in summary['worst_queries']:
                f.write(f"- **{q['query']}**: hit@5={q['hit@5']:.2f}, relevant={q['relevant_count']}/5, domain={q['top_domain']}\n")
            f.write("\n")
    
    logger.info(f"✅ Markdown report saved to {md_path}")


def main():
    parser = argparse.ArgumentParser(description="Auto Insurance RAG Evaluation")
    parser.add_argument(
        "--collection",
        type=str,
        default="auto_insurance_v2_clean",
        help="Qdrant collection name (default: auto_insurance_v2_clean)"
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=Path("results/auto_insurance"),
        help="Directory to save reports (default: results/auto_insurance)"
    )
    parser.add_argument(
        "--translate-zh",
        type=int,
        default=0,
        help="Enable translation for Chinese queries (1=enabled, 0=disabled, default: 0)"
    )
    parser.add_argument(
        "--eval-mode",
        type=str,
        default="normal",
        choices=["normal", "translated"],
        help="Evaluation mode: 'normal' (use original query for relevance) or 'translated' (use translated query for relevance, default: normal)"
    )
    
    args = parser.parse_args()
    
    # Get Qdrant credentials
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        logger.error("QDRANT_URL environment variable is required")
        return 1
    
    # Run evaluation
    evaluator = RAGEvaluator(args.collection, qdrant_url, qdrant_api_key)
    translate_zh = bool(args.translate_zh)
    eval_mode = args.eval_mode
    
    summary = evaluator.run_evaluation(translate_zh=translate_zh, eval_mode=eval_mode)
    
    # Generate reports (with appropriate suffix)
    if translate_zh and eval_mode == "translated":
        report_name = "EVAL_REPORT_TRANSLATED"
    elif translate_zh:
        report_name = "EVAL_REPORT_TRANSLATION"
    else:
        report_name = "EVAL_REPORT_BASELINE"
    
    generate_reports(summary, args.report_dir, report_name=report_name)
    
    return 0 if summary["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
