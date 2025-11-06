#!/usr/bin/env python3
"""
固定 ON 配置验证脚本
自动执行：Judger 20条人审 + Canary 10分钟实验 + 报告生成
"""

import sys
import time
import json
import subprocess
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_banner(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_api():
    """检查 API 是否运行"""
    import requests
    try:
        resp = requests.get("http://localhost:8080/health", timeout=2)
        return resp.ok
    except:
        return False

def run_judger_sampling(n=20):
    """运行 Judger 采样"""
    print_banner("步骤 1: 生成 Judger 评测批次")
    
    script_path = Path(__file__).parent / "judger_sample.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--n", str(n), "--strategy", "mixed"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.returncode != 0:
            print(f"⚠️  采样失败: {result.stderr}")
            return None
        
        # 提取批次ID（从输出中解析）
        for line in result.stdout.split('\n'):
            if "批次ID:" in line:
                batch_id = line.split("批次ID:")[1].strip()
                return batch_id
        
        # 如果没找到，用当前时间生成
        return datetime.now().strftime("%Y%m%d_%H%M%S")
        
    except Exception as e:
        print(f"⚠️  执行失败: {e}")
        return None

def check_judger_votes(batch_id, timeout=300):
    """等待并检查 Judger 投票结果"""
    print_banner("步骤 2: 等待 Judger 人工评审")
    
    reports_dir = Path(__file__).parent.parent / "reports"
    votes_file = reports_dir / f"judge_votes_{batch_id}.jsonl"
    
    print(f"📋 批次ID: {batch_id}")
    print(f"🔗 评审链接: http://localhost:8080/judge?batch={batch_id}")
    print(f"\n⏳ 等待人工评审完成（超时 {timeout}s）...")
    print("   按 Ctrl+C 跳过等待，直接进入 Canary 测试\n")
    
    start_time = time.time()
    try:
        while time.time() - start_time < timeout:
            if votes_file.exists():
                with open(votes_file) as f:
                    votes_count = sum(1 for line in f if line.strip())
                
                if votes_count >= 20:
                    print(f"\n✅ 收到 {votes_count} 条评审")
                    
                    # 获取评审结果
                    import requests
                    try:
                        resp = requests.get(f"http://localhost:8080/judge/summary.json?batch={batch_id}")
                        if resp.ok:
                            summary = resp.json()
                            return summary
                    except:
                        pass
                    
                    return {"verdict": "UNKNOWN", "better_rate": 0.0}
                
                print(f"   已收到 {votes_count}/20 条评审...", end='\r')
            
            time.sleep(2)
        
        print(f"\n⏱️  等待超时，跳过人工评审环节")
        return None
        
    except KeyboardInterrupt:
        print(f"\n⏭️  用户跳过等待")
        return None

def run_canary_test():
    """运行 Canary 10分钟测试"""
    print_banner("步骤 3: 运行 Canary 10分钟实验")
    
    script_path = Path(__file__).parent / "run_canary_10min.py"
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            timeout=660  # 11 minutes
        )
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"⚠️  Canary 测试失败: {e}")
        return False

def generate_final_report(judger_summary, canary_success):
    """生成最终报告"""
    print_banner("步骤 4: 生成最终报告")
    
    reports_dir = Path(__file__).parent.parent / "reports"
    canary_file = reports_dir / "autotuner_canary.json"
    
    # 读取 Canary 结果
    canary_data = {}
    if canary_file.exists():
        with open(canary_file) as f:
            canary_data = json.load(f)
    
    # 构建最终报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "on_config": {
            "page_index": True,
            "reranker": True
        },
        "judger": judger_summary or {
            "verdict": "SKIPPED",
            "note": "人工评审未完成或被跳过"
        },
        "canary": {
            "success": canary_success,
            "data": canary_data
        },
        "overall_verdict": determine_overall_verdict(judger_summary, canary_data, canary_success)
    }
    
    # 保存报告
    output_file = reports_dir / "on_config_validation_report.json"
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 打印总结
    print_report_summary(report)
    
    return report

def determine_overall_verdict(judger_summary, canary_data, canary_success):
    """综合判断总体结果"""
    verdicts = []
    
    # Judger 评估
    if judger_summary:
        verdicts.append(judger_summary.get("verdict", "UNKNOWN"))
    
    # Canary 评估
    if canary_success and canary_data:
        # 检查统计显著性
        p_value = canary_data.get("p_value", 1.0)
        delta_recall = canary_data.get("delta_recall", 0.0)
        
        if p_value < 0.05 and delta_recall >= 0.05:
            verdicts.append("PASS")
        else:
            verdicts.append("WARN")
    
    # 综合判断
    if not verdicts:
        return "NO_DATA"
    elif all(v == "PASS" for v in verdicts):
        return "PASS"
    elif any(v == "FAIL" for v in verdicts):
        return "FAIL"
    else:
        return "WARN"

def print_report_summary(report):
    """打印报告摘要"""
    print(f"\n[ON CONFIG] PageIndex={report['on_config']['page_index']} Reranker={report['on_config']['reranker']}")
    
    judger = report["judger"]
    if judger.get("verdict") == "SKIPPED":
        print(f"[JUDGER] SKIPPED - {judger.get('note', '')}")
    else:
        print(f"[JUDGER] samples={judger.get('total', 0)} verdict={judger.get('verdict', 'UNKNOWN')} better_rate={judger.get('better_rate', 0):.1%}")
    
    canary = report["canary"]["data"]
    if canary:
        print(f"[CANARY] ΔRecall={canary.get('delta_recall', 0):+.4f} ΔP95={canary.get('delta_p95_ms', 0):+.1f}ms p-value={canary.get('p_value', 1.0):.4f}")
    else:
        print(f"[CANARY] NO_DATA")
    
    print(f"[VERDICT] {report['overall_verdict']}")
    
    # 文件路径
    print(f"\n[REPORT] reports/on_config_validation_report.json")
    
    docs_dir = Path(__file__).parent.parent / "docs"
    if (docs_dir / "one_pager_fiqa.pdf").exists():
        print(f"[REPORT] docs/one_pager_fiqa.pdf")

def main():
    print_banner("固定 ON 配置验证 (PageIndex + Reranker)")
    
    # 检查 API
    print("🔍 检查服务状态...")
    if not check_api():
        print("❌ API 未运行，请先启动: bash launch.sh")
        return 1
    print("✅ API 正常运行\n")
    
    # 1. 生成 Judger 批次
    batch_id = run_judger_sampling(n=20)
    if not batch_id:
        print("❌ Judger 采样失败")
        judger_summary = None
    else:
        # 2. 等待人工评审（可跳过）
        judger_summary = check_judger_votes(batch_id, timeout=300)
    
    # 3. 运行 Canary 测试
    canary_success = run_canary_test()
    
    # 4. 生成最终报告
    report = generate_final_report(judger_summary, canary_success)
    
    print(f"\n{'='*60}")
    print("  验证完成")
    print(f"{'='*60}\n")
    
    return 0 if report["overall_verdict"] == "PASS" else 1

if __name__ == "__main__":
    sys.exit(main())

