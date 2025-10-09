#!/usr/bin/env python3
"""
验证 RAG QueryRewriter 集成的快速检查脚本
"""

import os
import sys
from pathlib import Path

def check_files():
    """检查所有必需文件是否存在"""
    
    files = [
        "pipeline/rag_pipeline.py",
        "labs/run_rag_rewrite_ab.py",
        "labs/run_rag_rewrite_ab_demo.py",
        "reports/rag_rewrite_ab.html",
        "modules/prompt_lab/query_rewriter.py",
        "modules/prompt_lab/contracts.py",
        "modules/prompt_lab/providers.py",
    ]
    
    print("=" * 60)
    print("🔍 检查文件存在性")
    print("=" * 60)
    
    all_exist = True
    for file_path in files:
        exists = os.path.exists(file_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {file_path}")
        if not exists:
            all_exist = False
    
    return all_exist


def check_imports():
    """检查关键模块导入"""
    
    print("\n" + "=" * 60)
    print("📦 检查模块导入")
    print("=" * 60)
    
    try:
        from pipeline.rag_pipeline import RAGPipeline, RAGPipelineConfig
        print("  ✓ pipeline.rag_pipeline")
    except Exception as e:
        print(f"  ✗ pipeline.rag_pipeline - {e}")
        return False
    
    try:
        from modules.prompt_lab.contracts import RewriteInput, RewriteOutput
        print("  ✓ modules.prompt_lab.contracts")
    except Exception as e:
        print(f"  ✗ modules.prompt_lab.contracts - {e}")
        return False
    
    try:
        from modules.prompt_lab.query_rewriter import QueryRewriter
        print("  ✓ modules.prompt_lab.query_rewriter")
    except Exception as e:
        print(f"  ✗ modules.prompt_lab.query_rewriter - {e}")
        return False
    
    try:
        from modules.prompt_lab.providers import MockProvider, ProviderConfig
        print("  ✓ modules.prompt_lab.providers")
    except Exception as e:
        print(f"  ✗ modules.prompt_lab.providers - {e}")
        return False
    
    return True


def quick_functional_test():
    """快速功能测试"""
    
    print("\n" + "=" * 60)
    print("🧪 快速功能测试")
    print("=" * 60)
    
    try:
        from pipeline.rag_pipeline import RAGPipeline, RAGPipelineConfig
        from modules.prompt_lab.contracts import RewriteInput
        from modules.prompt_lab.query_rewriter import QueryRewriter
        from modules.prompt_lab.providers import MockProvider, ProviderConfig
        
        # Test 1: QueryRewriter with MockProvider
        print("\n  [1/3] 测试 QueryRewriter...")
        provider = MockProvider(ProviderConfig())
        rewriter = QueryRewriter(provider)
        
        input_data = RewriteInput(query="What is ETF?")
        output = rewriter.rewrite(input_data, mode="json")
        
        print(f"    ✓ 查询改写成功: '{input_data.query}' -> '{output.query_rewrite}'")
        
        # Test 2: RAGPipelineConfig
        print("\n  [2/3] 测试 RAGPipelineConfig...")
        config = RAGPipelineConfig(
            search_config={"retriever": {"type": "vector", "top_k": 500}},
            rewrite_enabled=True,
            use_mock_provider=True
        )
        print(f"    ✓ 配置创建成功: rewrite_enabled={config.rewrite_enabled}")
        
        # Test 3: RAGPipeline initialization
        print("\n  [3/3] 测试 RAGPipeline 初始化...")
        pipeline = RAGPipeline(config)
        print(f"    ✓ Pipeline 初始化成功")
        
        return True
        
    except Exception as e:
        print(f"  ✗ 功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_html_report():
    """检查 HTML 报告内容"""
    
    print("\n" + "=" * 60)
    print("📊 检查 HTML 报告")
    print("=" * 60)
    
    html_path = "reports/rag_rewrite_ab.html"
    
    if not os.path.exists(html_path):
        print(f"  ✗ 报告文件不存在: {html_path}")
        return False
    
    with open(html_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ("Recall@10" in content, "包含 Recall@10 指标"),
        ("P95 延迟" in content, "包含 P95 延迟指标"),
        ("命中率" in content, "包含命中率指标"),
        ("Group A" in content, "包含 Group A 数据"),
        ("Group B" in content, "包含 Group B 数据"),
        ("Delta" in content, "包含 Delta 对比"),
        ("DEMO MODE" in content, "标记为 Demo 模式"),
    ]
    
    all_passed = True
    for check, desc in checks:
        status = "✓" if check else "✗"
        print(f"  {status} {desc}")
        if not check:
            all_passed = False
    
    file_size = os.path.getsize(html_path)
    print(f"\n  文件大小: {file_size / 1024:.1f} KB")
    
    return all_passed


def main():
    """主函数"""
    
    print()
    print("╔" + "═" * 58 + "╗")
    print("║" + " " * 10 + "RAG QueryRewriter 集成验证工具" + " " * 17 + "║")
    print("╚" + "═" * 58 + "╝")
    print()
    
    results = []
    
    # 1. 检查文件
    results.append(("文件检查", check_files()))
    
    # 2. 检查导入
    results.append(("导入检查", check_imports()))
    
    # 3. 功能测试
    results.append(("功能测试", quick_functional_test()))
    
    # 4. HTML 报告检查
    results.append(("报告检查", check_html_report()))
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 总结")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
    
    all_passed = all(passed for _, passed in results)
    
    print()
    if all_passed:
        print("🎉 " + "=" * 54 + " 🎉")
        print("║  所有检查通过！RAG QueryRewriter 集成成功！" + " " * 13 + "║")
        print("🎉 " + "=" * 54 + " 🎉")
        print()
        print("📖 快速开始:")
        print("   1. Demo 模式: python labs/run_rag_rewrite_ab_demo.py")
        print("   2. 查看报告: open reports/rag_rewrite_ab.html")
        print("   3. 阅读文档: cat RAG_REWRITER_AB_TEST_README.md")
        return 0
    else:
        print("⚠️  部分检查未通过，请检查上述错误信息")
        return 1


if __name__ == "__main__":
    sys.exit(main())
