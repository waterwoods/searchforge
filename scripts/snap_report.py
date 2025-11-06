#!/usr/bin/env python3
"""截取评审报告（优先#verdict-card，否则首屏）+ 生成案例对比卡"""
import sys, time, subprocess, shutil, json, argparse
from pathlib import Path
from urllib.parse import quote

try: from playwright.sync_api import sync_playwright; PW=1
except: PW=0
try: from selenium import webdriver; SE=1
except: SE=0
try: from PIL import Image; PIL=1
except: PIL=0

def get_size(path):
    if not PIL or not Path(path).exists(): return None
    try:
        img = Image.open(path)
        return f"{img.width}×{img.height}"
    except: return None

def try_playwright(url, out):
    with sync_playwright() as p:
        b = p.chromium.launch()
        g = b.new_page(viewport={"width":1000,"height":800}, device_scale_factor=2)
        g.goto(url, wait_until="networkidle", timeout=30000); time.sleep(1)
        try: c = g.query_selector("#verdict-card"); (c or g).screenshot(path=out)
        except: g.screenshot(path=out, full_page=False)
        b.close()
    return get_size(out)

def try_selenium(url, out):
    opts = webdriver.ChromeOptions(); opts.add_argument('--headless')
    opts.add_argument('--window-size=1000,800')
    d = webdriver.Chrome(options=opts); d.get(url); time.sleep(2)
    d.save_screenshot(str(out)); d.quit()
    return get_size(out)

def try_wkhtmltoimage(url, out):
    if not shutil.which('wkhtmltoimage'): return None
    subprocess.run(['wkhtmltoimage', '--width', '1200', url, str(out)], 
                   capture_output=True, timeout=30)
    return get_size(out)


def generate_case_screenshots(n_cases=3):
    """生成对比案例截图"""
    # 加载对比数据
    compare_file = Path(__file__).parent.parent / "reports" / "compare_batch_latest.json"
    if not compare_file.exists():
        print(f"⚠️  对比数据不存在: {compare_file}")
        return []
    
    with open(compare_file) as f:
        data = json.load(f)
    
    # 选择 best_rank_delta 最大的 n_cases 个
    items = sorted(data.get("items", []), key=lambda x: x.get("best_rank_delta", 0), reverse=True)
    top_cases = items[:n_cases]
    
    if not top_cases:
        print("⚠️  没有找到有效案例")
        return []
    
    # 创建输出目录
    cases_dir = Path(__file__).parent.parent / "docs" / "cases"
    cases_dir.mkdir(parents=True, exist_ok=True)
    
    screenshots = []
    base_url = "http://localhost:8080/judge/report"
    
    print(f"📸 生成 {len(top_cases)} 个案例截图...")
    
    for i, case in enumerate(top_cases, 1):
        query = case.get("query", "")
        case_id = case.get("id", i-1)
        rank_delta = case.get("best_rank_delta", 0)
        
        # 构建 URL（带锚点或查询参数定位到具体案例）
        case_url = f"{base_url}#q-{case_id}"
        
        out_path = cases_dir / f"case{i}.png"
        
        print(f"  [{i}/{len(top_cases)}] 截取案例 (delta=+{rank_delta}): {query[:50]}...")
        
        # 截图
        size = None
        if PW: 
            size = try_playwright(case_url, out_path, wait_for_selector=f"#q-{case_id}")
        elif SE: 
            size = try_selenium(case_url, out_path)
        elif shutil.which('wkhtmltoimage'): 
            size = try_wkhtmltoimage(case_url, out_path)
        
        if size:
            screenshots.append({
                "path": str(out_path),
                "query": query,
                "rank_delta": rank_delta,
                "trigger_reason": case.get("trigger_reason", "none"),
                "size": size
            })
            print(f"    ✓ {out_path} ({size})")
        else:
            print(f"    ⚠️  截图失败")
    
    return screenshots


def generate_one_pager(screenshots):
    """生成一页卡 PDF"""
    if not screenshots:
        print("⚠️  没有截图，跳过 PDF 生成")
        return None
    
    output_pdf = Path(__file__).parent.parent / "docs" / "one_pager_cases.pdf"
    
    # 使用简化版 HTML -> PDF 生成
    html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>ON=PageIndex+Reranker: 3 个真实提升案例</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            max-width: 1000px;
            margin: 40px auto;
            padding: 20px;
            background: white;
        }}
        h1 {{
            color: #1976d2;
            border-bottom: 3px solid #4caf50;
            padding-bottom: 10px;
        }}
        .case {{
            margin: 30px 0;
            page-break-inside: avoid;
        }}
        .case-header {{
            background: #e8f5e9;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 15px;
        }}
        .metric {{
            display: inline-block;
            background: #4caf50;
            color: white;
            padding: 5px 12px;
            border-radius: 3px;
            margin-right: 10px;
            font-weight: bold;
        }}
        .trigger {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 5px 12px;
            border-radius: 3px;
            font-size: 0.9em;
        }}
        img {{
            max-width: 100%;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .query {{
            font-size: 1.1em;
            font-weight: bold;
            color: #333;
            margin-bottom: 10px;
        }}
    </style>
</head>
<body>
    <h1>ON=PageIndex+Reranker：3 个真实提升案例</h1>
    <p style="color:#666; font-size:0.95em;">以下是从真实查询集中选出的排名提升最显著的 3 个案例，展示了 PageIndex + Reranker 组合相比 Baseline 的优势。</p>
"""
    
    for i, shot in enumerate(screenshots, 1):
        html_content += f"""
    <div class="case">
        <div class="case-header">
            <div class="query">案例 {i}: {shot['query']}</div>
            <span class="metric">排名提升: +{shot['rank_delta']}</span>
            <span class="trigger">触发原因: {shot['trigger_reason']}</span>
        </div>
        <img src="../{Path(shot['path']).relative_to(Path(__file__).parent.parent)}" alt="Case {i} Screenshot">
    </div>
"""
    
    html_content += """
</body>
</html>
"""
    
    # 写入临时 HTML
    temp_html = Path(__file__).parent.parent / "docs" / "temp_cases.html"
    with open(temp_html, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"\n📄 生成 PDF...")
    
    # 尝试转换为 PDF
    pdf_generated = False
    
    # 方法 1: wkhtmltopdf
    if shutil.which('wkhtmltopdf'):
        try:
            subprocess.run([
                'wkhtmltopdf', 
                '--page-size', 'A4',
                '--margin-top', '20mm',
                '--margin-bottom', '20mm',
                str(temp_html), 
                str(output_pdf)
            ], capture_output=True, timeout=60)
            if output_pdf.exists():
                pdf_generated = True
                print(f"✓ PDF 已生成: {output_pdf}")
        except Exception as e:
            print(f"⚠️  wkhtmltopdf 失败: {e}")
    
    # 方法 2: Playwright PDF
    if not pdf_generated and PW:
        try:
            with sync_playwright() as p:
                b = p.chromium.launch()
                page = b.new_page()
                page.goto(f"file://{temp_html.absolute()}")
                page.pdf(path=str(output_pdf), format='A4', margin={'top': '20mm', 'bottom': '20mm'})
                b.close()
            pdf_generated = True
            print(f"✓ PDF 已生成: {output_pdf}")
        except Exception as e:
            print(f"⚠️  Playwright PDF 失败: {e}")
    
    if not pdf_generated:
        print(f"⚠️  PDF 生成失败，HTML 保存在: {temp_html}")
        print(f"   手动打开 HTML 并打印为 PDF: {temp_html}")
        return None
    
    # 清理临时文件
    # temp_html.unlink()
    
    return str(output_pdf)


def main():
    parser = argparse.ArgumentParser(description="截取评审报告或生成案例对比卡")
    parser.add_argument("--cases", type=int, default=0, 
                       help="生成 N 个案例截图和 one-pager PDF")
    parser.add_argument("--url", type=str, default="http://localhost:8080/judge/report",
                       help="报告 URL")
    parser.add_argument("--out", type=str, default="docs/judge_verdict.png",
                       help="输出路径")
    args = parser.parse_args()
    
    # 案例模式
    if args.cases > 0:
        screenshots = generate_case_screenshots(args.cases)
        pdf_path = generate_one_pager(screenshots)
        
        case_files = ", ".join([f"case{i+1}.png" for i in range(len(screenshots))])
        pdf_status = pdf_path if pdf_path else "(未生成)"
        
        print(f"\n[DELIVERY] {pdf_status} | docs/cases/{case_files} | /judge/report")
        return
    
    # 普通模式：单张截图
    url = args.url
    out = args.out
    Path(out).parent.mkdir(parents=True, exist_ok=True)

    size = None
    if PW: size = try_playwright(url, out)
    elif SE: size = try_selenium(url, out)
    elif shutil.which('wkhtmltoimage'): size = try_wkhtmltoimage(url, out)

    if size:
        print(f"✓ Screenshot saved: {out} ({size})")
    else:
        # Fallback: open browser and ask user to screenshot manually
        print(f"⚠️  Auto-screenshot not available (install playwright: pip install playwright && playwright install)")
        try:
            subprocess.run(['open', url], stderr=subprocess.DEVNULL)
            print(f"   Opening {url} in browser...")
            print(f"   请手动截图并保存到: {out}")
        except:
            print(f"   请手动打开 {url} 并截图保存到: {out}")


if __name__ == "__main__":
    main()
