#!/usr/bin/env python3
"""
AutoTuner完整演示：展示ef_search参数从AutoTuner状态到Qdrant的完整链路
"""

import os
import sys
import time
import json

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from modules.search.search_pipeline import SearchPipeline, _autotuner_state, _get_env_config

def autotuner_demo():
    """AutoTuner完整演示"""
    
    # 设置环境变量
    os.environ["TUNER_ENABLED"] = "1"
    os.environ["TUNER_SAMPLE_SEC"] = "1"
    os.environ["TUNER_COOLDOWN_SEC"] = "1"
    os.environ["SLO_P95_MS"] = "500"  # 低SLO来触发建议
    os.environ["SLO_RECALL_AT10"] = "0.30"
    os.environ["FORCE_HYBRID_ON"] = "0"
    os.environ["CE_CACHE_SIZE"] = "0"
    os.environ["FORCE_CE_ON"] = "1"
    
    print("=== AutoTuner 完整演示 ===")
    print("目标：证明 ef_search 参数从 AutoTuner 状态正确传递到 Qdrant")
    print()
    
    # 检查初始配置
    env_config = _get_env_config()
    print("📋 环境配置:")
    print(f"  TUNER_ENABLED: {env_config['tuner_enabled']}")
    print(f"  SLO_P95_MS: {env_config['slo_p95_ms']}ms")
    print(f"  SLO_RECALL_AT10: {env_config['slo_recall_at10']}")
    print(f"  初始 ef_search: {_autotuner_state['current_ef_search']}")
    print()
    
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
        "How to invest in stocks?",
        "What is dividend yield?",
        "How to analyze stock performance?"
    ]
    
    print(f"🚀 开始运行 {len(queries)} 个查询...")
    print()
    
    # 捕获输出
    import io
    import contextlib
    
    stdout_capture = io.StringIO()
    
    with contextlib.redirect_stdout(stdout_capture):
        for i, query in enumerate(queries):
            print(f"--- 查询 {i+1}: {query[:40]}... ---")
            
            # 运行搜索
            results = pipeline.search(
                query=query,
                collection_name="beir_fiqa_full_ta",
                candidate_k=50
            )
            
            # 显示当前状态
            print(f"  📊 当前状态:")
            print(f"    ef_search: {_autotuner_state['current_ef_search']}")
            print(f"    metrics_window: {len(_autotuner_state['metrics_window'])} 个样本")
            print(f"    suggestions_made: {_autotuner_state['suggestions_made']}")
            print(f"    suggestions_applied: {_autotuner_state['suggestions_applied']}")
            
            # 小延迟
            time.sleep(0.3)
    
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
    
    print("\n" + "="*60)
    print("📈 实验结果分析")
    print("="*60)
    
    print(f"\n📊 事件统计:")
    print(f"  总事件数: {len(events)}")
    print(f"  RETRIEVE_VECTOR事件: {len(retrieve_vector_events)}")
    print(f"  AUTOTUNER_SUGGEST事件: {len(autotuner_events)}")
    print(f"  PARAMS_APPLIED事件: {len(params_applied_events)}")
    
    # 分析ef_search值变化
    ef_search_values = [event.get('params', {}).get('ef_search', 128) for event in retrieve_vector_events]
    unique_ef_values = list(set(ef_search_values))
    
    print(f"\n🔧 EF Search参数变化:")
    print(f"  所有ef_search值: {ef_search_values}")
    print(f"  唯一ef_search值: {unique_ef_values}")
    print(f"  变化次数: {len(unique_ef_values)}")
    
    if len(unique_ef_values) > 1:
        print("  ✅ 成功！ef_search参数发生了变化")
    else:
        print("  ❌ 失败！ef_search参数未发生变化")
    
    # 分析AutoTuner建议
    if autotuner_events:
        print(f"\n🎯 AutoTuner建议详情:")
        for i, event in enumerate(autotuner_events):
            params = event.get('params', {})
            suggest = params.get('suggest', {})
            print(f"  建议 {i+1}:")
            print(f"    p95_ms: {params.get('p95_ms', 'N/A')}")
            print(f"    recall_at10: {params.get('recall_at10', 'N/A')}")
            print(f"    建议ef_search: {suggest.get('ef_search', 'N/A')}")
    
    # 分析参数应用
    if params_applied_events:
        print(f"\n⚙️ 参数应用详情:")
        for i, event in enumerate(params_applied_events):
            applied = event.get('applied', {})
            print(f"  应用 {i+1}:")
            print(f"    applied: {applied.get('applied', False)}")
            print(f"    {applied.get('old_ef_search', 'N/A')} → {applied.get('new_ef_search', 'N/A')}")
            print(f"    reason: {applied.get('reason', 'N/A')}")
    
    # 验证参数链路
    print(f"\n🔗 参数链路验证:")
    print(f"  1. AutoTuner状态: current_ef_search = {_autotuner_state['current_ef_search']}")
    print(f"  2. SearchPipeline: 从AutoTuner状态获取ef_search")
    print(f"  3. VectorSearch: 传递ef_search到Qdrant客户端")
    print(f"  4. Qdrant: 接收hnsw_ef参数")
    
    # 检查最后几个RETRIEVE_VECTOR事件的ef_search值
    if len(retrieve_vector_events) >= 3:
        last_events = retrieve_vector_events[-3:]
        print(f"\n📋 最后3个RETRIEVE_VECTOR事件的ef_search值:")
        for i, event in enumerate(last_events):
            ef_search = event.get('params', {}).get('ef_search', 'N/A')
            print(f"  {i+1}. ef_search = {ef_search}")
    
    print(f"\n🎉 演示完成！")
    print(f"  最终ef_search: {_autotuner_state['current_ef_search']}")
    print(f"  总建议数: {_autotuner_state['suggestions_made']}")
    print(f"  总应用数: {_autotuner_state['suggestions_applied']}")
    
    return {
        "events": events,
        "autotuner_events": autotuner_events,
        "params_applied_events": params_applied_events,
        "ef_search_values": ef_search_values,
        "final_ef_search": _autotuner_state['current_ef_search']
    }

if __name__ == "__main__":
    results = autotuner_demo()
