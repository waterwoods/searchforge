#!/usr/bin/env python3
"""快速验证 ON 配置是否正确工作"""

import requests
import json

BASE_URL = "http://localhost:8080"
TEST_QUERY = "What is an ETF?"

def test_mode(mode):
    """测试指定模式"""
    print(f"\n🔍 测试 mode={mode}:")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/search",
            json={"query": TEST_QUERY, "top_k": 3},
            params={"mode": mode},
            timeout=10
        )
        
        if resp.ok:
            data = resp.json()
            print(f"  ✅ 成功 | 延迟: {data.get('latency_ms', 0):.1f}ms")
            print(f"     答案数: {len(data.get('answers', []))}")
            return True
        else:
            print(f"  ❌ 失败: {resp.status_code}")
            return False
            
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False

def check_api():
    """检查 API 健康状态"""
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        return resp.ok
    except:
        return False

def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  快速配置验证 (ON = PageIndex + Reranker)")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    
    # 检查 API
    print("\n📡 检查 API 状态...")
    if not check_api():
        print("❌ API 未运行，请先启动: bash launch.sh")
        return 1
    print("✅ API 正常运行")
    
    # 测试 OFF 模式
    off_success = test_mode("off")
    
    # 测试 ON 模式
    on_success = test_mode("on")
    
    # 测试默认模式
    default_success = test_mode(None)
    
    # 总结
    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  验证结果:")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  OFF 模式: {'✅ PASS' if off_success else '❌ FAIL'}")
    print(f"  ON 模式:  {'✅ PASS' if on_success else '❌ FAIL'}")
    print(f"  默认模式: {'✅ PASS' if default_success else '❌ FAIL'}")
    
    if off_success and on_success:
        print("\n[ON CONFIG] PageIndex+Reranker 配置正常")
        print("[READY] 可以运行完整验证: bash run_on_config_test.sh")
        return 0
    else:
        print("\n[ERROR] 配置验证失败")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())

