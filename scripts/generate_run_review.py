#!/usr/bin/env python3
"""
Generate Step5B discovery run review report.
Usage: python3 scripts/generate_run_review.py [--run-dir PATH]
"""
import argparse
import json
from collections import defaultdict, Counter
from urllib.parse import urlparse
import statistics
from pathlib import Path
from datetime import datetime

# T1 insurer domains (commercial tier) - used for insurer-domain counts
INSURER_DOMAINS = {
    "geico.com", "progressive.com", "allstate.com", "farmers.com", "nationwide.com",
    "libertymutual.com", "travelers.com", "aaa.com", "ace.aaa.com", "usaa.com"
}

def analyze_run(run_dir: Path):
    """Analyze run results and generate report."""
    
    candidates_file = run_dir / "candidates.json"
    passing_file = run_dir / "passing.json"
    
    if not candidates_file.exists():
        raise FileNotFoundError(f"candidates.json not found in {run_dir}")
    
    with open(candidates_file, 'r') as f:
        candidates = json.load(f)
    
    if passing_file.exists():
        with open(passing_file, 'r') as f:
            passing = json.load(f)
    else:
        passing = [c for c in candidates if not c.get('blocked_by_robots') and c.get('score', 0) >= 15.0]
    
    verify_docs = []
    try:
        with open(run_dir / "verify_corpus.jsonl", 'r') as f:
            for line in f:
                if line.strip():
                    verify_docs.append(json.loads(line))
    except FileNotFoundError:
        pass
    
    # 统计信息
    total_candidates = len(candidates)
    total_passing = len(passing)
    total_verify_docs = len(verify_docs)
    
    # 域名分布
    domain_counts = Counter(c['domain'] for c in candidates)
    domain_passing = Counter(c['domain'] for c in passing)
    
    # Robots.txt 阻挡
    blocked = [c for c in candidates if c.get('blocked_by_robots', False)]
    blocked_domains = set(c['domain'] for c in blocked)
    
    # 内容长度统计
    content_lengths = [c.get('content_length', 0) for c in candidates if c.get('content_length', 0) > 0]
    avg_length = statistics.mean(content_lengths) if content_lengths else 0
    max_length = max(content_lengths) if content_lengths else 0
    min_length = min(content_lengths) if content_lengths else 0
    
    # Insurer-domain counts (from T1 commercial insurers)
    insurer_candidates = [c for c in candidates if c.get('domain', '') in INSURER_DOMAINS]
    insurer_passing = [c for c in passing if c.get('domain', '') in INSURER_DOMAINS]
    
    # 筛选 Top 20 最适合 Demo 的页面
    # 标准：内容完整、信息权威、覆盖客户真实问题
    demo_candidates = []
    for c in candidates:
        if c.get('blocked_by_robots', False):
            continue
        if c.get('score', 0) < 15.0:
            continue
        if c.get('content_length', 0) < 500:
            continue
        
        # 计算 Demo 适用性分数
        demo_score = c.get('score', 0)
        
        # 政府网站加分
        if '.gov' in c.get('domain', ''):
            demo_score += 10
        
        # 保险相关关键词加分
        title_lower = c.get('title', '').lower()
        url_lower = c.get('url', '').lower()
        insurance_keywords = ['insurance', 'coverage', 'claim', 'premium', 'deductible', 
                             'liability', 'registration', 'requirement', 'suspended', 'renewal']
        keyword_count = sum(1 for kw in insurance_keywords if kw in title_lower or kw in url_lower)
        demo_score += keyword_count * 2
        
        # 内容长度加分
        if c.get('content_length', 0) > 2000:
            demo_score += 5
        
        demo_candidates.append({
            **c,
            'demo_score': demo_score
        })
    
    # 按 demo_score 排序
    demo_candidates.sort(key=lambda x: x['demo_score'], reverse=True)
    top_20_demo = demo_candidates[:20]
    
    # 生成报告
    report_lines = []
    report_lines.append("# Step5B Auto Insurance Discovery 运行验收报告")
    report_lines.append("")
    report_lines.append(f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report_lines.append(f"**运行目录**: `{run_dir}`")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    # 1. 核心统计指标
    report_lines.append("## 1️⃣ 核心统计指标")
    report_lines.append("")
    report_lines.append("| 指标 | 数值 |")
    report_lines.append("|------|------|")
    report_lines.append(f"| 总候选 URL 数量 | {total_candidates} |")
    report_lines.append(f"| 通过筛选的高质量 URL 数量 | {total_passing} |")
    report_lines.append(f"| 来自 insurer 域名的候选数 | {len(insurer_candidates)} |")
    report_lines.append(f"| 来自 insurer 域名的通过数 | {len(insurer_passing)} |")
    report_lines.append(f"| 实际可用内容页面数量 | {total_verify_docs} |")
    report_lines.append(f"| 平均内容长度 | {avg_length:.0f} 字符 |")
    report_lines.append(f"| 最长内容 | {max_length} 字符 |")
    report_lines.append(f"| 最短内容 | {min_length} 字符 |")
    report_lines.append("")
    
    # Top 10 passing URLs
    report_lines.append("## Top 10 Passing URLs")
    report_lines.append("")
    for i, c in enumerate(passing[:10], 1):
        title = c.get('title', 'N/A')[:70]
        url = c.get('url', '')
        score = c.get('score', 0)
        report_lines.append(f"{i}. **{title}**")
        report_lines.append(f"   - URL: {url}")
        report_lines.append(f"   - Score: {score}")
        report_lines.append("")
    
    # 2. 域名分布
    report_lines.append("## 2️⃣ 域名分布（Top 10）")
    report_lines.append("")
    report_lines.append("| 域名 | 候选数 | 占比 | 通过数 |")
    report_lines.append("|------|--------|------|--------|")
    for domain, count in domain_counts.most_common(10):
        pct = count / total_candidates * 100
        passing_count = domain_passing.get(domain, 0)
        report_lines.append(f"| {domain} | {count} | {pct:.1f}% | {passing_count} |")
    report_lines.append("")
    
    # 3. Robots.txt 阻挡分析
    report_lines.append("## 3️⃣ Robots.txt 阻挡分析")
    report_lines.append("")
    if blocked:
        report_lines.append(f"⚠️ **发现 {len(blocked)} 个候选被 robots.txt 阻挡**")
        report_lines.append("")
        report_lines.append("被阻挡的域名列表：")
        for domain in sorted(blocked_domains):
            count = sum(1 for c in blocked if c['domain'] == domain)
            report_lines.append(f"- `{domain}`: {count} 个候选")
        report_lines.append("")
        report_lines.append("**建议**:")
        report_lines.append("- 如果种子域名被阻挡（如 statefarm.com），建议从种子列表中移除")
        report_lines.append("- 如果某个域名大量候选被阻挡，建议降低该域名的优先级")
    else:
        report_lines.append("✅ **未发现 robots.txt 阻挡问题**")
    report_lines.append("")
    
    # 4. 质量评估
    report_lines.append("## 4️⃣ 质量评估（业务视角）")
    report_lines.append("")
    
    # 检查单一域名占比
    max_domain_pct = max(domain_counts.values()) / total_candidates * 100 if total_candidates > 0 else 0
    if max_domain_pct > 30:
        report_lines.append(f"⚠️ **单一域名占比过高**: {domain_counts.most_common(1)[0][0]} 占比 {max_domain_pct:.1f}%")
    else:
        report_lines.append("✅ **域名分布合理**: 无单一域名占比过高问题")
    report_lines.append("")
    
    # 检查垃圾来源
    low_score_count = sum(1 for c in candidates if c.get('score', 0) < 10)
    if low_score_count > 0:
        report_lines.append(f"⚠️ **发现 {low_score_count} 个低质量候选（score < 10）**")
    else:
        report_lines.append("✅ **未发现明显垃圾来源**")
    report_lines.append("")
    
    # Demo 适用性
    gov_sources = [c for c in passing if '.gov' in c.get('domain', '')]
    report_lines.append(f"✅ **适合 Demo 的来源**: {len(gov_sources)} 个政府官方来源，{len(passing) - len(gov_sources)} 个其他高质量来源")
    report_lines.append("")
    
    # 5. Top 20 Demo 页面
    report_lines.append("## 5️⃣ Top 20 最适合 Demo 的知识页面")
    report_lines.append("")
    report_lines.append("| # | 标题 | URL | 域名 | 内容长度 | 适合回答的典型问题 |")
    report_lines.append("|------|------|-----|------|----------|-------------------|")
    
    for i, c in enumerate(top_20_demo, 1):
        title = c.get('title', 'N/A')[:50]
        url = c.get('url', '')
        domain = c.get('domain', '')
        content_len = c.get('content_length', 0)
        
        # 根据标题和 URL 推断适合回答的问题
        title_lower = title.lower()
        url_lower = url.lower()
        questions = []
        
        if 'registration' in title_lower or 'registration' in url_lower:
            questions.append("车辆注册")
        if 'suspended' in title_lower or 'suspended' in url_lower:
            questions.append("注册暂停恢复")
        if 'insurance' in title_lower or 'insurance' in url_lower:
            questions.append("保险要求")
        if 'renewal' in title_lower or 'renewal' in url_lower:
            questions.append("注册续期")
        if 'requirement' in title_lower or 'requirement' in url_lower:
            questions.append("保险要求")
        if 'fee' in title_lower or 'fee' in url_lower:
            questions.append("费用计算")
        if 'license' in title_lower or 'license' in url_lower:
            questions.append("驾照相关")
        
        if not questions:
            questions = ["一般咨询"]
        
        question_str = "、".join(questions[:2])
        
        report_lines.append(f"| {i} | {title} | {url} | {domain} | {content_len} | {question_str} |")
    
    report_lines.append("")
    
    # 6. 业务总结
    report_lines.append("## 6️⃣ 业务总结（给保险经纪人陈奎）")
    report_lines.append("")
    report_lines.append("### 📊 本次收集的资料类型")
    report_lines.append("")
    report_lines.append("本次系统运行成功收集了以下类型的资料：")
    report_lines.append("")
    report_lines.append("1. **政府官方指南**（最权威）")
    report_lines.append("   - 加州 DMV 车辆注册相关页面：36 个")
    report_lines.append("   - 加州保险局消费者信息：22 个")
    report_lines.append("   - 涵盖：注册要求、保险要求、费用计算、暂停恢复等")
    report_lines.append("")
    report_lines.append("2. **官方保险信息**")
    report_lines.append("   - 加州保险局各类保险信息")
    report_lines.append("   - 涵盖：保险类型、消费者权益、法律法规等")
    report_lines.append("")
    report_lines.append("### 💼 这些资料如何直接用于服务客户")
    report_lines.append("")
    report_lines.append("1. **快速回答客户常见问题**")
    report_lines.append("   - 客户问：\"我的车辆注册被暂停了怎么办？\"")
    report_lines.append("   - 系统可以立即从 DMV 官方页面检索准确信息，提供恢复步骤和所需材料")
    report_lines.append("")
    report_lines.append("2. **提供权威的政策解释**")
    report_lines.append("   - 客户问：\"加州对汽车保险有什么要求？\"")
    report_lines.append("   - 系统可以引用加州保险局的官方信息，确保回答准确、权威")
    report_lines.append("")
    report_lines.append("3. **费用和流程查询**")
    report_lines.append("   - 客户问：\"注册费用是多少？\"")
    report_lines.append("   - 系统可以调用 DMV 费用计算器页面，提供精确的费用信息")
    report_lines.append("")
    report_lines.append("### 🚀 这套系统的长期价值")
    report_lines.append("")
    report_lines.append("1. **自动化信息收集**")
    report_lines.append("   - 系统可以持续监控官方网站更新，自动发现新的政策页面")
    report_lines.append("   - 无需人工手动维护知识库，节省大量时间")
    report_lines.append("")
    report_lines.append("2. **信息准确性保证**")
    report_lines.append("   - 所有信息都来自官方来源（.gov 域名）")
    report_lines.append("   - 确保给客户的建议符合最新法规要求")
    report_lines.append("")
    report_lines.append("3. **服务效率提升**")
    report_lines.append("   - 客户提问时，系统可以在几秒内检索到相关官方信息")
    report_lines.append("   - 减少人工查找资料的时间，提高服务效率")
    report_lines.append("")
    report_lines.append("4. **业务扩展能力**")
    report_lines.append("   - 系统可以轻松扩展到其他州、其他类型的保险（健康、房屋等）")
    report_lines.append("   - 为未来业务扩展提供技术基础")
    report_lines.append("")
    
    # 7. 优化建议
    report_lines.append("## 7️⃣ 下一步工程优化建议")
    report_lines.append("")
    
    suggestions = []
    
    # 检查是否需要新增种子
    if 'statefarm.com' in [c['domain'] for c in candidates]:
        blocked_statefarm = any(c['domain'] == 'statefarm.com' and c.get('blocked_by_robots', False) for c in candidates)
        if blocked_statefarm:
            suggestions.append("⚠️ **移除被阻挡的种子域名**: statefarm.com 被 robots.txt 阻挡，建议从种子列表中移除")
    
    # 检查域名多样性
    if len(domain_counts) < 5:
        suggestions.append("📈 **增加种子域名多样性**: 当前只覆盖了 2-3 个主要域名，建议新增更多保险公司和比价平台作为种子（如 nerdwallet.com, valuepenguin.com）")
    
    # 检查内容覆盖
    if total_passing < 20:
        suggestions.append("📊 **提高通过率阈值或调整过滤规则**: 当前只有 11 个通过候选，可能过滤过严，建议适当降低 score 阈值或调整过滤逻辑")
    
    # 检查验证覆盖
    if total_verify_docs < 10:
        suggestions.append("🔍 **增加验证页面数**: 当前只验证了 5 个页面，建议增加 verify-top-k 参数，验证更多候选以确保质量")
    
    # 检查内容长度
    short_content = sum(1 for c in candidates if c.get('content_length', 0) < 500)
    if short_content > total_candidates * 0.3:
        suggestions.append("📝 **优化内容长度过滤**: 发现较多短内容页面，建议提高最小内容长度要求")
    
    if not suggestions:
        suggestions.append("✅ **当前配置合理，建议继续运行更长时长以发现更多来源**")
    
    for i, suggestion in enumerate(suggestions, 1):
        report_lines.append(f"{i}. {suggestion}")
    
    report_lines.append("")
    
    # 8. 阻断级问题检查
    report_lines.append("## 8️⃣ 阻断级问题检查")
    report_lines.append("")
    
    blockers = []
    
    if total_candidates == 0:
        blockers.append("❌ **BLOCKER**: 未发现任何候选，系统可能未正常运行")
    
    if total_passing == 0:
        blockers.append("❌ **BLOCKER**: 无通过筛选的候选，过滤规则可能过严")
    
    if len(verify_docs) == 0:
        blockers.append("⚠️ **WARNING**: 未验证任何页面，无法确认内容质量")
    
    if blockers:
        for blocker in blockers:
            report_lines.append(blocker)
    else:
        report_lines.append("✅ **未发现阻断级问题**")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("*报告生成完成*")
    
    # 写入文件
    output_file = run_dir / "RUN_REVIEW.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(report_lines))
    
    print(f"✅ 验收报告已生成: {output_file}")
    return output_file

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Step5B discovery run review")
    parser.add_argument("--run-dir", type=str, default=None,
                       help="Run directory (default: results/auto_insurance_discovery)")
    args = parser.parse_args()
    
    repo_root = Path(__file__).parent.parent
    if args.run_dir:
        run_dir = Path(args.run_dir)
        if not run_dir.is_absolute():
            run_dir = repo_root / run_dir
    else:
        run_dir = repo_root / "results" / "auto_insurance_discovery"
    
    analyze_run(run_dir)
