#!/usr/bin/env python3
"""验证依赖项检查：确保一键验证脚本可以正常运行"""
import sys
import subprocess
from pathlib import Path

def check(name, fn):
    """检查单项并输出结果"""
    try:
        result = fn()
        status = "✅" if result else "⚠️"
        print(f"{status} {name}")
        return result
    except Exception as e:
        print(f"❌ {name}: {e}")
        return False

def check_python():
    """检查 Python 版本"""
    return sys.version_info >= (3, 8)

def check_requests():
    """检查 requests 库"""
    try:
        import requests
        return True
    except ImportError:
        return False

def check_api():
    """检查 API 是否运行"""
    try:
        import requests
        r = requests.get("http://localhost:8080/health", timeout=2)
        return r.ok
    except:
        return False

def check_qdrant():
    """检查 Qdrant 连接"""
    try:
        import requests
        r = requests.get("http://localhost:6333/collections", timeout=2)
        if r.ok:
            colls = r.json().get("result", {}).get("collections", [])
            return any(c.get("name") == "beir_fiqa_full_ta" for c in colls)
    except:
        return False

def check_screenshot():
    """检查截图工具"""
    try:
        from playwright.sync_api import sync_playwright
        return True
    except:
        try:
            from selenium import webdriver
            return True
        except:
            import shutil
            return shutil.which('wkhtmltoimage') is not None

def check_scripts():
    """检查必需脚本文件"""
    root = Path(__file__).parent.parent
    scripts = [
        root / "scripts" / "run_full_validation.py",
        root / "scripts" / "judger_sample.py",
        root / "scripts" / "run_canary_10min.py",
        root / "scripts" / "snap_report.py",
    ]
    return all(s.exists() for s in scripts)

def check_matplotlib():
    """检查 matplotlib (用于 PDF 生成)"""
    try:
        import matplotlib
        return True
    except ImportError:
        return False

def main():
    print("╔" + "═"*58 + "╗")
    print("║" + " "*15 + "依赖项检查" + " "*28 + "║")
    print("╚" + "═"*58 + "╝\n")
    
    results = {}
    results['python'] = check("Python 3.8+", check_python)
    results['requests'] = check("requests 库", check_requests)
    results['matplotlib'] = check("matplotlib 库 (PDF生成)", check_matplotlib)
    results['scripts'] = check("必需脚本文件", check_scripts)
    results['api'] = check("API 服务 (localhost:8080)", check_api)
    results['qdrant'] = check("Qdrant + beir_fiqa_full_ta", check_qdrant)
    results['screenshot'] = check("截图工具 (playwright/selenium/wkhtmltoimage)", check_screenshot)
    
    print("\n" + "="*60)
    
    critical = ['python', 'requests', 'scripts', 'api']
    optional = ['matplotlib', 'qdrant', 'screenshot']
    
    critical_ok = all(results.get(k, False) for k in critical)
    
    if critical_ok:
        print("✅ 核心依赖已满足，可以运行验证流程")
        if not results.get('matplotlib'):
            print("⚠️  缺少 matplotlib：PDF 生成会失败")
            print("   安装: pip install matplotlib")
        if not results.get('qdrant'):
            print("⚠️  Qdrant 未连接：会使用模拟数据")
            print("   启动: docker-compose up -d qdrant")
        if not results.get('screenshot'):
            print("⚠️  无截图工具：需手动截图")
            print("   安装 playwright: pip install playwright && playwright install chromium")
            print("   或安装 selenium: pip install selenium")
        
        print("\n🚀 运行验证:")
        print("   python3 scripts/run_full_validation.py")
        return 0
    else:
        print("❌ 缺少核心依赖，无法运行验证")
        if not results.get('python'):
            print("   Python 版本需要 >= 3.8")
        if not results.get('requests'):
            print("   安装: pip install requests")
        if not results.get('scripts'):
            print("   错误: 脚本文件缺失")
        if not results.get('api'):
            print("   启动 API: bash launch.sh")
        return 1

if __name__ == "__main__":
    sys.exit(main())

