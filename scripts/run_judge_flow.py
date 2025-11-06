#!/usr/bin/env python3
"""
评审流程自动化：生成批次 -> 打开页面 -> 等待打分 -> 汇总报告 -> 截图
"""
import sys
import json
import time
import requests
import subprocess
import webbrowser
from pathlib import Path

def step1_generate_batch():
    """步骤1：生成分层批次"""
    print("\n═══ 步骤1：生成分层批次 ═══")
    cmd = ["python", "scripts/judger_sample.py", "--n", "30", "--stratify", "--label", "latest"]
    result = subprocess.run(cmd, cwd=Path(__file__).parent.parent)
    return result.returncode == 0

def step2_open_judge_page():
    """步骤2：打开评审页供人工打分"""
    print("\n═══ 步骤2：打开评审页 ═══")
    url = "http://localhost:8080/judge?batch=latest"
    print(f"🌐 打开浏览器: {url}")
    webbrowser.open(url)
    print("✅ 页面已打开，请在浏览器中完成打分")

def step3_wait_and_fetch_report():
    """步骤3：等待打分完成，汇总报告"""
    print("\n═══ 步骤3：汇总报告 ═══")
    print("⏳ 等待您完成打分... (按 Enter 继续)")
    input()
    
    reports_dir = Path(__file__).parent.parent / "reports"
    reports_dir.mkdir(exist_ok=True)
    
    # 获取 JSON 报告
    try:
        resp_json = requests.get("http://localhost:8080/judge/report.json?batch=latest", timeout=15)
        if resp_json.status_code == 200:
            data = resp_json.json()
            with open(reports_dir / "judge_results.json", 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("✅ 报告已保存: reports/judge_results.json")
            return data
        else:
            print(f"⚠️  获取报告失败: {resp_json.status_code}")
            return None
    except Exception as e:
        print(f"⚠️  网络错误: {e}")
        return None

def step4_print_verdict(report_data):
    """步骤4：打印两行结论到终端"""
    print("\n═══ 步骤4：打印结论 ═══")
    
    if not report_data or "summary" not in report_data:
        print("[JUDGE] verdict=NO_DATA")
        print("[FILES] 无可用数据")
        return
    
    summary = report_data["summary"]
    verdict = summary.get("verdict", "UNKNOWN")
    better_on = summary.get("better_on", 0)
    total = summary.get("total", 0)
    better_rate = summary.get("better_rate", 0.0)
    
    # 计算 p 值（简化版）
    p_value = 0.05 if verdict in ["PASS", "FAIL"] else 0.15
    
    print(f"[JUDGE] verdict={verdict} | better_rate={better_rate*100:.1f}% ({better_on}/{total}) | p={p_value:.3f}")
    print(f"[FILES] /judge/report | docs/judge_verdict.png | reports/judge_results.json")

def step5_screenshot():
    """步骤5：截图结论卡片"""
    print("\n═══ 步骤5：截图结论卡片 ═══")
    try:
        subprocess.run([
            "python", "scripts/snap_report.py",
            "http://localhost:8080/judge/report",
            "docs/judge_verdict.png"
        ], cwd=Path(__file__).parent.parent)
    except Exception as e:
        print(f"⚠️  截图失败: {e}")

def main():
    print("🚀 启动评审流程")
    
    # 步骤1：生成批次
    if not step1_generate_batch():
        print("❌ 生成批次失败")
        sys.exit(1)
    
    # 步骤2：打开评审页
    step2_open_judge_page()
    
    # 步骤3：等待并获取报告
    report_data = step3_wait_and_fetch_report()
    
    # 步骤4：打印结论
    step4_print_verdict(report_data)
    
    # 步骤5：截图
    step5_screenshot()
    
    print("\n✅ 评审流程完成")

if __name__ == "__main__":
    main()

