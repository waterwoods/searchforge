#!/usr/bin/env python3
"""
Verify Auto Insurance Collection
=================================
验证 Qdrant Cloud 中的 auto_insurance_v1 集合

Usage:
    python scripts/verify_auto_insurance_collection.py
"""

import os
import sys
import logging
import random
from typing import List, Dict

# Load environment variables from .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, skip (will use system env vars)
    pass

from qdrant_client import QdrantClient

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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Fixed model name
MODEL_NAME = "BAAI/bge-m3"
FALLBACK_MODEL = "mixedbread-ai/mxbai-embed-large-v1"


def get_qdrant_client() -> QdrantClient:
    """Initialize Qdrant client from environment"""
    qdrant_url = os.getenv("QDRANT_URL")
    qdrant_api_key = os.getenv("QDRANT_API_KEY")
    
    if not qdrant_url:
        raise ValueError("QDRANT_URL environment variable is required")
    
    client_kwargs = {"url": qdrant_url}
    if qdrant_api_key:
        client_kwargs["api_key"] = qdrant_api_key
    
    return QdrantClient(**client_kwargs)


def sample_documents(client: QdrantClient, collection_name: str, n: int = 5) -> List[Dict]:
    """Sample random documents from collection"""
    try:
        # Get collection info
        collection_info = client.get_collection(collection_name)
        total_points = collection_info.points_count
        
        if total_points == 0:
            logger.warning(f"Collection {collection_name} is empty")
            return []
        
        logger.info(f"Collection {collection_name} has {total_points} points")
        
        # Scroll to get random points
        points = []
        try:
            # Use scroll to get all points, then sample
            scroll_result = client.scroll(
                collection_name=collection_name,
                limit=total_points
            )
            all_points = scroll_result[0]
            if all_points:
                sample_size = min(n, len(all_points))
                points = random.sample(all_points, sample_size)
        except Exception as e:
            logger.warning(f"Failed to scroll points: {e}")
        
        return points
    except Exception as e:
        logger.error(f"Failed to sample documents: {e}")
        return []


def print_sample_info(points: List):
    """Print information about sampled points"""
    logger.info("\n" + "="*80)
    logger.info("Sample Documents (5 random)")
    logger.info("="*80)
    
    for i, point in enumerate(points, 1):
        payload = point.payload
        logger.info(f"\n[{i}] Point ID: {point.id}")
        logger.info(f"    Language: {payload.get('language', 'unknown')}")
        logger.info(f"    Title: {payload.get('title', 'N/A')[:80]}")
        logger.info(f"    Source URL: {payload.get('source_url', 'N/A')[:80]}")
        logger.info(f"    Content Type: {payload.get('content_type', 'N/A')}")
        text = payload.get('text', '')
        if text:
            logger.info(f"    Text Preview: {text[:100]}...")


def get_embedder():
    """Get embedding model with fallback"""
    # Try sentence-transformers first
    if SENTENCE_TRANSFORMERS_AVAILABLE:
        try:
            logger.info(f"Using sentence-transformers for {MODEL_NAME}")
            return SentenceTransformer(MODEL_NAME), False
        except Exception as e:
            logger.warning(f"sentence-transformers failed: {e}")
    
    # Try fastembed with fallback
    if FASTEMBED_AVAILABLE:
        try:
            return TextEmbedding(model_name=MODEL_NAME), True
        except Exception as e:
            logger.warning(f"fastembed doesn't support {MODEL_NAME}, using fallback")
            return TextEmbedding(model_name=FALLBACK_MODEL), True
    
    raise RuntimeError("No embedding library available")

def embed_query(embedder, use_fastembed: bool, text: str):
    """Embed query text"""
    if use_fastembed:
        return list(embedder.embed([text]))[0]
    else:
        return embedder.encode([text], convert_to_numpy=True)[0].tolist()

def test_cross_language_search(
    client: QdrantClient,
    collection_name: str,
    embedder,
    use_fastembed: bool
):
    """Test cross-language search (Chinese query -> English docs)"""
    logger.info("\n" + "="*80)
    logger.info("Cross-Language Search Test")
    logger.info("="*80)
    
    # Test queries in different languages
    test_queries = [
        ("中文查询：加州最低汽车保险要求是什么？", "zh"),
        ("English query: What is the minimum auto insurance requirement in California?", "en"),
        ("中文查询：如何申请理赔？", "zh"),
        ("English query: How to file a claim?", "en"),
    ]
    
    for query_text, query_lang in test_queries:
        logger.info(f"\n🔍 Query ({query_lang}): {query_text}")
        
        try:
            # Generate query embedding
            query_embedding = embed_query(embedder, use_fastembed, query_text)
            
            # Search
            results = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=5
            )
            
            logger.info(f"  Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                payload = result.payload
                logger.info(f"    [{i}] Score: {result.score:.4f}")
                logger.info(f"        Language: {payload.get('language', 'unknown')}")
                logger.info(f"        Title: {payload.get('title', 'N/A')[:60]}")
                logger.info(f"        URL: {payload.get('source_url', 'N/A')[:60]}")
        
        except Exception as e:
            logger.error(f"  Search failed: {e}")


def verify_collection(client: QdrantClient, collection_name: str):
    """Verify collection exists and has data"""
    try:
        collections = client.get_collections()
        collection_names = [c.name for c in collections.collections]
        
        if collection_name not in collection_names:
            logger.error(f"❌ Collection {collection_name} not found")
            logger.info(f"Available collections: {collection_names}")
            return False
        
        collection_info = client.get_collection(collection_name)
        logger.info(f"✅ Collection {collection_name} exists")
        logger.info(f"   Points: {collection_info.points_count}")
        logger.info(f"   Vectors: {collection_info.vectors_count}")
        logger.info(f"   Status: {collection_info.status}")
        
        if collection_info.points_count == 0:
            logger.warning(f"⚠️  Collection is empty")
            return False
        
        return True
    except Exception as e:
        logger.error(f"Failed to verify collection: {e}")
        return False


def main():
    collection_name = os.getenv("QDRANT_COLLECTION", "auto_insurance_v1")
    
    logger.info("="*80)
    logger.info("Auto Insurance Collection Verification")
    logger.info("="*80)
    logger.info(f"Collection: {collection_name}")
    
    try:
        # Initialize clients
        logger.info("\n1. Initializing Qdrant client...")
        client = get_qdrant_client()
        logger.info("✅ Qdrant client initialized")
        
        # Verify collection
        logger.info("\n2. Verifying collection...")
        if not verify_collection(client, collection_name):
            return 1
        
        # Sample documents
        logger.info("\n3. Sampling documents...")
        points = sample_documents(client, collection_name, n=5)
        if points:
            print_sample_info(points)
        else:
            logger.warning("⚠️  No documents sampled")
        
        # Test cross-language search
        logger.info("\n4. Testing cross-language search...")
        try:
            embedder, use_fastembed = get_embedder()
            logger.info(f"✅ Embedding model loaded")
            test_cross_language_search(client, collection_name, embedder, use_fastembed)
        except Exception as e:
            logger.error(f"Failed to test cross-language search: {e}")
            import traceback
            logger.error(traceback.format_exc())
        
        logger.info("\n" + "="*80)
        logger.info("✅ Verification completed")
        logger.info("="*80)
        
        return 0
    
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
