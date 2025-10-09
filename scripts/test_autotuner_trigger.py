#!/usr/bin/env python3
"""
测试AutoTuner触发条件
"""

import os
import sys
import time
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline, _autotuner_state, _get_env_config

def test_autotuner_trigger():
    """测试AutoTuner触发条件"""
    
    # 设置环境变量
    os.environ["TUNER_ENABLED"] = "1"
    os.environ["TUNER_SAMPLE_SEC"] = "1"
    os.environ["TUNER_COOLDOWN_SEC"] = "1"
    os.environ["SLO_P95_MS"] = "500"  # 低SLO来触发建议
    os.environ["SLO_RECALL_AT10"] = "0.30"
    os.environ["FORCE_HYBRID_ON"] = "0"
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["FORCE_CE_ON"] = "1"
    
    print("=== AutoTuner 触发条件测试 ===")
    
    # 检查配置
    env_config = _get_env_config()
    print(f"TUNER_ENABLED: {env_config['tuner_enabled']}")
    print(f"TUNER_SAMPLE_SEC: {env_config['tuner_sample_sec']}")
    print(f"需要的最小样本数: 3")
    
    # 初始化pipeline
    config = {
        "retriever": {
            "type": "vector",
            "top_k": 10,
            "ef_search": 128
        },
        "reranker": {
            "type": "cross_encoder",
            "model": "cross-encoder/ms-marco-MiniLM-L-2-v2",
            "top_k": 50
        }
    }
    
    pipeline = SearchPipeline(config)
    
    # 准备查询
    queries = [
        "What is ETF expense ratio?",
        "How to calculate portfolio returns?", 
        "What are the risks of cryptocurrency investment?",
        "What is bond yield?",
        "How to diversify portfolio?",
        "What is mutual fund?",
        "How to invest in stocks?"
    ]
    
    print(f"\n运行 {len(queries)} 个查询来收集足够的样本...")
    
    # 捕获输出
    import io
    import contextlib
    
    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        for i, query in enumerate(queries):
            print(f"\n--- 查询 {i+1}: {query[:30]}... ---")
            
            # 运行搜索
            results = pipeline.search(
                query=query,
                collection_name="beir_fiqa_full_ta",
                candidate_k=50
            )
            
            # 检查状态
            print(f"Metrics window: {len(_autotuner_state['metrics_window'])} 个样本")
            print(f"Suggestions made: {_autotuner_state['suggestions_made']}")
            print(f"Current ef_search: {_autotuner_state['current_ef_search']}")
            
            # 检查是否满足触发条件
            if len(_autotuner_state['metrics_window']) >= 3:
                print("✅ 满足触发条件 (≥3个样本)")
            else:
                print(f"❌ 不满足触发条件 (需要≥3个样本，当前{len(_autotuner_state['metrics_window'])})")
            
            # 小延迟
            time.sleep(0.2)
    
    # 解析输出
    captured_output = stdout_capture.getvalue()
    
    # 解析JSON事件
    events = []
    for line in captured_output.split('\n'):
        line = line.strip()
        if line and line.startswith('{'):
            try:
                event = json.loads(line)
                events.append(event)
            except json.JSONDecodeError:
                continue
    
    # 分析事件
    autotuner_events = [e for e in events if e.get('event') == 'AUTOTUNER_SUGGEST']
    params_applied_events = [e for e in events if e.get('event') == 'PARAMS_APPLIED']
    retrieve_vector_events = [e for e in events if e.get('event') == 'RETRIEVE_VECTOR']
    
    print(f"\n=== 事件分析 ===")
    print(f"总事件数: {len(events)}")
    print(f"RETRIEVE_VECTOR事件: {len(retrieve_vector_events)}")
    print(f"AUTOTUNER_SUGGEST事件: {len(autotuner_events)}")
    print(f"PARAMS_APPLIED事件: {len(params_applied_events)}")
    
    if autotuner_events:
        print(f"\n=== AutoTuner建议详情 ===")
        for i, event in enumerate(autotuner_events):
            params = event.get('params', {})
            suggest = params.get('suggest', {})
            print(f"建议 {i+1}:")
            print(f"  ef_search: {suggest.get('ef_search', 'N/A')}")
            print(f"  p95_ms: {params.get('p95_ms', 'N/A')}")
            print(f"  recall_at10: {params.get('recall_at10', 'N/A')}")
    
    if params_applied_events:
        print(f"\n=== 参数应用详情 ===")
        for i, event in enumerate(params_applied_events):
            applied = event.get('applied', {})
            print(f"应用 {i+1}:")
            print(f"  applied: {applied.get('applied', False)}")
            print(f"  old_ef_search: {applied.get('old_ef_search', 'N/A')}")
            print(f"  new_ef_search: {applied.get('new_ef_search', 'N/A')}")
            print(f"  reason: {applied.get('reason', 'N/A')}")
    
    # 检查ef_search值变化
    ef_search_values = [event.get('params', {}).get('ef_search', 128) for event in retrieve_vector_events]
    print(f"\n=== EF Search值变化 ===")
    print(f"ef_search值: {ef_search_values}")
    if len(set(ef_search_values)) > 1:
        print("✅ EF Search值发生了变化")
    else:
        print("❌ EF Search值未发生变化")
    
    return {
        "events": events,
        "autotuner_events": autotuner_events,
        "params_applied_events": params_applied_events,
        "ef_search_values": ef_search_values
    }

if __name__ == "__main__":
    results = test_autotuner_trigger()
