#!/usr/bin/env python3
"""
test_langsmith_tracing.py - 测试 LangSmith Tracing 配置

这个脚本会：
1. 检查环境变量是否正确设置
2. 检查 langsmith 包是否安装
3. 运行一个简单的测试来验证 tracing 是否工作
"""

import os
import sys
from pathlib import Path

# Load .env file before anything else
from dotenv import load_dotenv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file from project root
env_path = project_root / '.env'
if env_path.exists():
    load_dotenv(env_path, override=False)
    print(f"✅ 已加载 .env 文件: {env_path}")
else:
    print(f"⚠️  .env 文件不存在: {env_path}")

def check_env_vars():
    """检查环境变量是否设置"""
    print("=" * 60)
    print("步骤 1: 检查环境变量")
    print("=" * 60)
    
    tracing_v2 = os.getenv("LANGCHAIN_TRACING_V2", "").lower()
    api_key = os.getenv("LANGCHAIN_API_KEY", "")
    project = os.getenv("LANGCHAIN_PROJECT", "")
    
    print(f"LANGCHAIN_TRACING_V2: {tracing_v2}")
    print(f"LANGCHAIN_API_KEY: {'✅ 已设置' if api_key else '❌ 未设置'} {'(' + api_key[:8] + '...)' if api_key else ''}")
    print(f"LANGCHAIN_PROJECT: {project if project else '❌ 未设置'}")
    
    is_enabled = tracing_v2 in ("true", "1", "yes", "on") and api_key
    print(f"\nTracing 状态: {'✅ 已启用' if is_enabled else '❌ 未启用'}")
    
    if not is_enabled:
        print("\n⚠️  提示：请确保在 .env 文件中设置了以下变量：")
        print("  LANGCHAIN_TRACING_V2=true")
        print("  LANGCHAIN_API_KEY=ls-your-key-here")
        print("  LANGCHAIN_PROJECT=searchforge-mortgage (或 searchforge-ops)")
        return False
    
    return True


def check_langsmith_import():
    """检查 langsmith 包是否安装"""
    print("\n" + "=" * 60)
    print("步骤 2: 检查 langsmith 包")
    print("=" * 60)
    
    try:
        import langsmith
        print(f"✅ langsmith 已安装，版本: {langsmith.__version__}")
        return True
    except ImportError:
        print("❌ langsmith 包未安装")
        print("\n请运行：pip install langsmith>=0.1.28")
        return False


def check_tracing_helper():
    """检查 tracing helper 模块"""
    print("\n" + "=" * 60)
    print("步骤 3: 检查 tracing helper 模块")
    print("=" * 60)
    
    try:
        from services.fiqa_api.observability.langsmith_tracing import maybe_traceable
        print("✅ tracing helper 模块导入成功")
        return True
    except Exception as e:
        print(f"❌ tracing helper 模块导入失败: {e}")
        return False


def test_mortgage_graph():
    """测试 mortgage graph tracing"""
    print("\n" + "=" * 60)
    print("步骤 4: 测试 Mortgage Graph Tracing")
    print("=" * 60)
    
    try:
        from services.fiqa_api.mortgage.graphs.single_home_graph import run_single_home_graph
        from services.fiqa_api.mortgage.schemas import SingleHomeAgentRequest, StressCheckRequest
        
        print("✅ 成功导入 run_single_home_graph")
        
        # 创建一个简单的测试请求
        test_request = SingleHomeAgentRequest(
            stress_request=StressCheckRequest(
                monthly_income=8000.0,
                other_debts_monthly=500.0,
                list_price=500000.0,
                down_payment_pct=0.20,
                zip_code="90210",
                state="CA"
            )
        )
        
        print("运行测试请求...")
        print("  收入: $8,000/月")
        print("  房价: $500,000")
        print("  首付: 20%")
        
        result = run_single_home_graph(test_request)
        
        print(f"✅ Graph 执行成功")
        print(f"   Stress Band: {result.stress_result.stress_band}")
        print(f"   DTI: {result.stress_result.dti_ratio:.3f}")
        print(f"\n💡 如果 tracing 已启用，你现在应该在 LangSmith UI 中看到 'single_home_graph_run' 的 trace")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ops_graph():
    """测试 ops graph tracing"""
    print("\n" + "=" * 60)
    print("步骤 5: 测试 Ops Copilot Graph Tracing")
    print("=" * 60)
    
    try:
        from services.fiqa_api.ops_copilot.graphs.system_health_graph import run_system_health_graph
        from services.fiqa_api.ops_copilot.schemas import SystemSnapshot
        from datetime import datetime
        
        print("✅ 成功导入 run_system_health_graph")
        
        # 创建一个简单的测试 snapshot
        test_snapshot = SystemSnapshot(
            service_name="test-service",
            environment="dev",  # Must be 'prod', 'staging', or 'dev'
            cpu_pct=75.0,
            mem_pct=80.0,
            p95_latency_ms=400.0,
            error_rate=0.02,
            qps=1000.0,
            disk_pct=70.0,
            timestamp=datetime.utcnow()
        )
        
        print("运行测试 snapshot...")
        print("  CPU: 75%")
        print("  Memory: 80%")
        print("  Latency: 400ms")
        
        result = run_system_health_graph(test_snapshot, request_id="test-request-123")
        
        print(f"✅ Graph 执行成功")
        print(f"   Health Band: {result['health_result'].band}")
        print(f"   Score: {result['health_result'].score:.1f}")
        print(f"\n💡 如果 tracing 已启用，你现在应该在 LangSmith UI 中看到 'system_health_graph_run' 的 trace")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("\n" + "🔍" * 30)
    print("LangSmith Tracing 配置测试")
    print("🔍" * 30 + "\n")
    
    # 检查环境变量
    if not check_env_vars():
        print("\n❌ 环境变量未正确配置，请检查 .env 文件")
        return 1
    
    # 检查 langsmith 包
    if not check_langsmith_import():
        print("\n❌ langsmith 包未安装")
        return 1
    
    # 检查 tracing helper
    if not check_tracing_helper():
        print("\n❌ tracing helper 模块有问题")
        return 1
    
    # 测试 mortgage graph
    print("\n" + "=" * 60)
    print("开始运行实际测试...")
    print("=" * 60)
    
    mortgage_ok = test_mortgage_graph()
    
    # 测试 ops graph
    ops_ok = test_ops_graph()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    
    if mortgage_ok and ops_ok:
        print("✅ 所有测试通过！")
        print("\n下一步：")
        print("1. 访问 https://smith.langchain.com/")
        print("2. 选择你的 project（" + os.getenv("LANGCHAIN_PROJECT", "未设置") + "）")
        print("3. 查看 'Traces' 页面，应该能看到刚才的测试 traces")
        return 0
    else:
        print("❌ 部分测试失败，请检查错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())

