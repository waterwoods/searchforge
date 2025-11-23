#!/usr/bin/env python3
"""
offline_strategy_eval.py - Batch Offline Experiment for Single-Home Agent + Strategy Lab

批量离线实验模块，用于用合成数据评估 single-home agent + strategy_lab 的表现。

用法:
    python3 experiments/offline_strategy_eval.py [--n-samples 100] [--seed 42]

输出:
    - 终端打印指标摘要
    - 各 stress_band 的样本数量和占比
    - 各 band 下 approval_score 的均值 / 分位数
    - Strategy Lab 中"有至少一个比 baseline 更安全方案"的样本比例
"""

import sys
import random
import argparse
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from statistics import mean, median

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from services.fiqa_api.mortgage import (
    run_stress_check,
    run_strategy_lab,
    run_safety_upgrade_flow,
    StressCheckRequest,
    StressCheckResponse,
    StrategyLabResult,
    SafetyUpgradeResult,
    StressBand,
)


# ============================================================================
# Configuration
# ============================================================================

# Mock ZIP codes and states used in existing tests
MOCK_ZIP_STATES = [
    ("90803", "CA"),  # Long Beach, CA
    ("92648", "CA"),  # Huntington Beach, CA
    ("90210", "CA"),  # Beverly Hills, CA
    ("73301", "TX"),  # Austin, TX
    ("78701", "TX"),  # Austin, TX
    ("98101", "WA"),  # Seattle, WA
    ("75001", "TX"),  # Dallas, TX
]

# Income ranges (monthly) to cover
INCOME_RANGES = [5000, 8000, 12000, 20000]  # 5k, 8k, 12k, 20k per month

# Price ranges (total home price)
PRICE_RANGES = [
    (400000, 600000),   # Lower range
    (600000, 800000),   # Mid range
    (800000, 1000000),  # Upper mid range
    (1000000, 1200000), # High range
]


# ============================================================================
# Synthetic Sample Generation
# ============================================================================

def generate_synthetic_cases(n: int, seed: int = 42) -> List[StressCheckRequest]:
    """
    生成合成样本用于批量实验。
    
    目标：大致让结果分布为 25% loose，25% ok，20% tight，30% high_risk
    
    策略：
    - 25% loose: 高收入 + 相对较低的房价（DTI < 36%）
    - 25% ok: 中等收入 + 精确控制的房价（DTI 在 36-43% 区间，房价约为年收入的 3.5-4.5 倍）
    - 20% tight: 中等收入 + 中等偏高房价（DTI 在 43-50% 区间）
    - 30% high_risk: 低收入 + 高房价，或中等收入 + 很高房价（DTI > 50%）
    
    Args:
        n: 生成的样本数量
        seed: 随机种子
    
    Returns:
        List[StressCheckRequest]: 生成的样本列表
    """
    random.seed(seed)
    
    cases: List[StressCheckRequest] = []
    
    # 按目标分布生成样本：loose 15%, ok 50%, tight 15%, high_risk 20%
    # 大幅增加 ok 样本占比，因为部分 ok 样本可能落入其他区间，最终目标仍是 20-30%
    n_loose = int(n * 0.15)     # 15% loose
    n_ok = int(n * 0.50)        # 50% ok (关键目标，大幅增加占比以提高最终 ok 比例)
    n_tight = int(n * 0.15)     # 15% tight
    n_high_risk = n - n_loose - n_ok - n_tight  # 剩余为 high_risk (~20%)
    
    # 生成 loose 样本：高收入 + 相对较低的房价（DTI < 36%）
    for i in range(n_loose):
        zip_code, state = random.choice(MOCK_ZIP_STATES)
        # 高收入 (12k-20k/month)
        income = random.choice([12000, 15000, 20000]) * random.uniform(0.90, 1.10)
        # 相对较低的房价，约为年收入的 2.8-3.8 倍（保证 DTI < 36%，不与 ok 重叠）
        annual_income = income * 12
        # 使用更低的倍数范围，确保与 ok 样本区分开
        list_price = annual_income * random.uniform(2.8, 3.8)
        down_payment_pct = random.uniform(0.20, 0.30)
        other_debts_monthly = income * random.uniform(0.0, 0.08)  # 低债务
        hoa_monthly = random.uniform(0.0, 400.0)
        risk_preference = random.choice(["conservative", "neutral", "aggressive"])
        
        cases.append(StressCheckRequest(
            monthly_income=income,
            other_debts_monthly=other_debts_monthly,
            list_price=list_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # 生成 ok 样本：中等收入 + 精确控制的房价（DTI 在 36-43% 区间）
    # 核心策略：使用平衡的房价/收入比（年收入的 4.0-4.5 倍），配合适中的首付比例和债务，让 DTI 稳定落在 ok 区间
    for i in range(n_ok):
        zip_code, state = random.choice(MOCK_ZIP_STATES)
        # 中等收入 (8k-13k/month)，避免极端值，集中在中等收入水平
        income = random.choice([8000, 9000, 10000, 11000, 12000, 13000]) * random.uniform(0.95, 1.05)
        # 基于年收入计算房价：使用平衡的倍数区间 4.0-4.5，确保 DTI 落在 ok 区间
        annual_income = income * 12
        # 使用更集中的倍数分布，重点在 4.1-4.4 区间（这个区间更容易产生 ok band）
        # 80% 样本：核心 ok 区间，倍数 4.1-4.4（最精确的 ok 区间）
        if random.random() < 0.80:
            price_multiplier = random.uniform(4.1, 4.4)
        # 15% 样本：略低倍数 4.0-4.2（ok 区间的低端，接近 loose-ok 边界）
        elif random.random() < 0.95:
            price_multiplier = random.uniform(4.0, 4.2)
        # 5% 样本：略高倍数 4.3-4.5（ok-tight 边界）
        else:
            price_multiplier = random.uniform(4.3, 4.5)
        list_price = annual_income * price_multiplier
        # 适中首付比例（18-22%），适中值以确保 DTI 稳定
        down_payment_pct = random.uniform(0.18, 0.22)
        # 适中的其他债务（5-10%），适度提高 DTI 使其稳定在 ok 区间
        other_debts_monthly = income * random.uniform(0.05, 0.10)
        hoa_monthly = random.uniform(0.0, 300.0)  # 适中的 HOA
        risk_preference = random.choice(["conservative", "neutral", "aggressive"])
        
        cases.append(StressCheckRequest(
            monthly_income=income,
            other_debts_monthly=other_debts_monthly,
            list_price=list_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # 生成 tight 样本：中等收入 + 中等偏高房价（DTI 在 43-50% 区间）
    for i in range(n_tight):
        zip_code, state = random.choice(MOCK_ZIP_STATES)
        # 中等收入 (7k-12k/month)
        income = random.choice([7000, 8000, 10000, 12000]) * random.uniform(0.90, 1.10)
        # 中等偏高房价，约为年收入的 4.5-5.5 倍
        annual_income = income * 12
        list_price = annual_income * random.uniform(4.5, 5.5)
        down_payment_pct = random.uniform(0.15, 0.22)
        other_debts_monthly = income * random.uniform(0.05, 0.15)
        hoa_monthly = random.uniform(0.0, 500.0)
        risk_preference = random.choice(["conservative", "neutral", "aggressive"])
        
        cases.append(StressCheckRequest(
            monthly_income=income,
            other_debts_monthly=other_debts_monthly,
            list_price=list_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # 生成 high_risk 样本：低收入 + 高房价，或中等收入 + 很高房价（DTI > 50%）
    # 调整：降低高倍数样本的比例，使 high_risk 占比更合理（~30-40%）
    for i in range(n_high_risk):
        zip_code, state = random.choice(MOCK_ZIP_STATES)
        # 70% 样本：低收入 + 高房价（房价约为年收入的 6.0-7.5 倍）
        # 30% 样本：中等收入 + 极高房价（房价约为年收入的 7.0-8.5 倍）
        if random.random() < 0.70:
            # 低收入 (5k-9k/month)
            income = random.choice([5000, 6000, 7000, 8000, 9000]) * random.uniform(0.85, 1.10)
            annual_income = income * 12
            list_price = annual_income * random.uniform(6.0, 7.5)
        else:
            # 中等收入 + 极高房价
            income = random.choice([8000, 10000, 12000]) * random.uniform(0.90, 1.10)
            annual_income = income * 12
            list_price = annual_income * random.uniform(7.0, 8.5)
        
        down_payment_pct = random.uniform(0.10, 0.20)  # 较低首付
        other_debts_monthly = income * random.uniform(0.08, 0.20)  # 较高债务
        hoa_monthly = random.uniform(0.0, 600.0)
        risk_preference = random.choice(["neutral", "aggressive"])  # 较少 conservative
        
        cases.append(StressCheckRequest(
            monthly_income=income,
            other_debts_monthly=other_debts_monthly,
            list_price=list_price,
            down_payment_pct=down_payment_pct,
            zip_code=zip_code,
            state=state,
            hoa_monthly=hoa_monthly,
            risk_preference=risk_preference,
        ))
    
    # 随机打乱顺序
    random.shuffle(cases)
    
    return cases


# ============================================================================
# Batch Processing
# ============================================================================

def run_batch_experiment(
    cases: List[StressCheckRequest],
    verbose: bool = False,
    args: Optional[argparse.Namespace] = None,
) -> List[Dict[str, Any]]:
    """
    批量运行 single-home agent 实验。
    
    Args:
        cases: 待测试的 StressCheckRequest 列表
        verbose: 是否打印详细信息
    
    Returns:
        List[Dict[str, Any]]: 每个样本的结果（包含 success, result, error 等）
    """
    results: List[Dict[str, Any]] = []
    
    print(f"\n开始批量实验，共 {len(cases)} 个样本...")
    start_time = time.time()
    
    for idx, case in enumerate(cases, 1):
        if verbose or idx % 10 == 0:
            print(f"  处理样本 {idx}/{len(cases)}...", end="\r")
        
        try:
            # 直接调用底层函数，绕过 run_single_home_agent 以避免 LLM 依赖问题
            # 这样可以获得相同的核心功能：stress_check + safety_upgrade + strategy_lab
            
            # Step 1: Run stress check
            stress_result = run_stress_check(case)
            
            # Step 2: Run safety upgrade flow
            safety_upgrade = None
            try:
                safety_upgrade = run_safety_upgrade_flow(
                    req=case,
                    max_candidates=5,
                )
            except Exception as e:
                # Safety upgrade 失败不应该影响整个流程
                if verbose:
                    print(f"      Safety upgrade failed: {e}")
            
            # Step 3: Run strategy lab
            strategy_lab = None
            try:
                strategy_lab = run_strategy_lab(
                    req=case,
                    max_scenarios=3,
                )
            except Exception as e:
                # Strategy lab 失败不应该影响整个流程
                if verbose:
                    print(f"      Strategy lab failed: {e}")
            
            # 组装结果（模拟 SingleHomeAgentResponse 的结构）
            result = {
                "stress_result": stress_result,
                "safety_upgrade": safety_upgrade,
                "strategy_lab": strategy_lab,
            }
            
            results.append({
                "success": True,
                "result": result,
                "error": None,
                "case": case,
            })
            
        except Exception as e:
            # 单个样本失败不应该中断整个实验
            import traceback
            error_msg = str(e)
            if args.verbose:
                print(f"\n  样本 {idx} 失败: {error_msg}")
                traceback.print_exc()
            results.append({
                "success": False,
                "result": None,
                "error": error_msg,
                "case": case,
            })
    
    elapsed_time = time.time() - start_time
    
    if verbose:
        print(f"\n批量实验完成，耗时 {elapsed_time:.2f} 秒")
    else:
        print(f"\n批量实验完成，耗时 {elapsed_time:.2f} 秒")
    
    return results


# ============================================================================
# Statistics & Metrics
# ============================================================================

def compute_statistics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    计算统计指标。
    
    Returns:
        Dict 包含各种指标
    """
    # 过滤成功的结果
    successful_results = [r for r in results if r["success"]]
    
    # 按 stress_band 分组
    band_counts: Dict[StressBand, int] = defaultdict(int)
    band_scores: Dict[StressBand, List[float]] = defaultdict(list)
    
    # Strategy Lab 相关统计
    strategy_lab_with_safer: int = 0  # 有至少一个更安全方案的样本数
    strategy_lab_total: int = 0  # 有 strategy_lab 的样本数
    
    for r in successful_results:
        result = r["result"]  # Dict with stress_result, safety_upgrade, strategy_lab
        stress_result: StressCheckResponse = result["stress_result"]
        
        # 统计 stress_band
        band = stress_result.stress_band
        band_counts[band] += 1
        
        # 统计 approval_score
        if stress_result.approval_score:
            score = stress_result.approval_score.score
            band_scores[band].append(score)
        
        # 统计 strategy_lab
        strategy_lab: Optional[StrategyLabResult] = result.get("strategy_lab")
        if strategy_lab:
            strategy_lab_total += 1
            baseline_band = strategy_lab.baseline_stress_band
            baseline_dti = strategy_lab.baseline_dti
            
            if baseline_band and baseline_dti is not None:
                # 检查是否有更安全的方案
                band_order = {"loose": 0, "ok": 1, "tight": 2, "high_risk": 3}
                baseline_order = band_order.get(baseline_band, 999)
                
                has_safer = False
                for scenario in strategy_lab.scenarios:
                    if scenario.stress_band and scenario.dti_ratio is not None:
                        scenario_order = band_order.get(scenario.stress_band, 999)
                        # 更安全 = 更低的 order 或者相同 order 但 DTI 更低
                        if scenario_order < baseline_order:
                            has_safer = True
                            break
                        elif scenario_order == baseline_order and scenario.dti_ratio < baseline_dti:
                            has_safer = True
                            break
                
                if has_safer:
                    strategy_lab_with_safer += 1
    
    # 计算总数和占比
    total_successful = len(successful_results)
    band_pct: Dict[StressBand, float] = {}
    for band, count in band_counts.items():
        band_pct[band] = (count / total_successful * 100) if total_successful > 0 else 0.0
    
    # 计算各 band 的 approval_score 统计
    band_score_stats: Dict[StressBand, Dict[str, float]] = {}
    for band, scores in band_scores.items():
        if scores:
            band_score_stats[band] = {
                "mean": mean(scores),
                "median": median(scores),
                "min": min(scores),
                "max": max(scores),
                "count": len(scores),
            }
    
    # Strategy Lab 比例
    strategy_lab_safer_pct = (
        (strategy_lab_with_safer / strategy_lab_total * 100) 
        if strategy_lab_total > 0 else 0.0
    )
    
    # 错误统计
    error_count = len(results) - total_successful
    error_pct = (error_count / len(results) * 100) if len(results) > 0 else 0.0
    
    return {
        "total_samples": len(results),
        "successful_samples": total_successful,
        "error_count": error_count,
        "error_pct": error_pct,
        "band_counts": dict(band_counts),
        "band_pct": band_pct,
        "band_score_stats": {k: v for k, v in band_score_stats.items()},
        "strategy_lab_total": strategy_lab_total,
        "strategy_lab_with_safer": strategy_lab_with_safer,
        "strategy_lab_safer_pct": strategy_lab_safer_pct,
    }


def print_statistics(stats: Dict[str, Any]) -> None:
    """
    打印统计摘要。
    """
    print("\n" + "=" * 80)
    print("批量离线实验 - 指标摘要")
    print("=" * 80)
    
    # 总体统计
    print(f"\n📊 总体统计:")
    print(f"   总样本数: {stats['total_samples']}")
    print(f"   成功样本: {stats['successful_samples']}")
    print(f"   错误样本: {stats['error_count']} ({stats['error_pct']:.1f}%)")
    
    # Stress Band 分布
    print(f"\n📈 Stress Band 分布:")
    band_order = ["loose", "ok", "tight", "high_risk"]
    for band in band_order:
        if band in stats['band_counts']:
            count = stats['band_counts'][band]
            pct = stats['band_pct'][band]
            print(f"   {band:12s}: {count:4d} ({pct:5.1f}%)")
    
    # Approval Score 统计（按 band）
    print(f"\n🎯 Approval Score 统计（按 band）:")
    for band in band_order:
        if band in stats['band_score_stats']:
            score_stats = stats['band_score_stats'][band]
            print(f"   {band:12s}:")
            print(f"      均值: {score_stats['mean']:.1f}")
            print(f"      中位数: {score_stats['median']:.1f}")
            print(f"      范围: [{score_stats['min']:.1f}, {score_stats['max']:.1f}]")
            print(f"      样本数: {score_stats['count']}")
    
    # Strategy Lab 统计
    print(f"\n🔬 Strategy Lab 统计:")
    print(f"   有 strategy_lab 的样本: {stats['strategy_lab_total']}")
    print(f"   有至少一个更安全方案: {stats['strategy_lab_with_safer']} ({stats['strategy_lab_safer_pct']:.1f}%)")
    
    print("\n" + "=" * 80)


# ============================================================================
# Main
# ============================================================================

def main():
    """主入口函数。"""
    parser = argparse.ArgumentParser(
        description="批量离线实验：评估 single-home agent + strategy_lab"
    )
    parser.add_argument(
        "--n-samples",
        type=int,
        default=100,
        help="生成的样本数量（默认: 100）"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="随机种子（默认: 42）"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="打印详细信息"
    )
    
    args = parser.parse_args()
    
    print("=" * 80)
    print("批量离线实验 - Single-Home Agent + Strategy Lab")
    print("=" * 80)
    print(f"\n配置:")
    print(f"  样本数量: {args.n_samples}")
    print(f"  随机种子: {args.seed}")
    print(f"  详细模式: {args.verbose}")
    
    # Step 1: 生成合成样本
    print(f"\n[步骤 1/3] 生成合成样本...")
    cases = generate_synthetic_cases(n=args.n_samples, seed=args.seed)
    print(f"  生成了 {len(cases)} 个样本")
    
    # Step 2: 批量运行实验
    print(f"\n[步骤 2/3] 批量运行实验...")
    results = run_batch_experiment(cases, verbose=args.verbose, args=args)
    
    # Step 3: 计算统计指标
    print(f"\n[步骤 3/3] 计算统计指标...")
    stats = compute_statistics(results)
    
    # 打印摘要
    print_statistics(stats)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

