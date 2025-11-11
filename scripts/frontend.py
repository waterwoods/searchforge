#!/usr/bin/env python3
"""
Frontend development scripts for SearchForge
Integrates Node.js frontend with Poetry environment
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
FRONTEND_DIR = PROJECT_ROOT / "src"

def run_command(cmd, cwd=None, shell=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            cmd, 
            cwd=cwd or PROJECT_ROOT, 
            shell=shell, 
            check=True, 
            capture_output=True, 
            text=True
        )
        print(f"✅ {cmd}")
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running: {cmd}")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def check_node_installed():
    """Check if Node.js is installed"""
    try:
        result = subprocess.run(["node", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js version: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Node.js not found. Please install Node.js 18+ first.")
    print("Visit: https://nodejs.org/")
    return False

def install_dependencies():
    """Install Node.js dependencies"""
    print("🔧 Installing frontend dependencies...")
    
    if not check_node_installed():
        return False
    
    # Check if package.json exists
    package_json = PROJECT_ROOT / "package.json"
    if not package_json.exists():
        print("❌ package.json not found. Please run this from the project root.")
        return False
    
    # Install dependencies
    run_command("npm install")
    print("✅ Frontend dependencies installed successfully!")
    return True

def start_dev_server():
    """Start the development server"""
    print("🚀 Starting SearchForge frontend development server...")
    
    if not check_node_installed():
        return False
    
    # Check if dependencies are installed
    node_modules = PROJECT_ROOT / "node_modules"
    if not node_modules.exists():
        print("📦 Installing dependencies first...")
        if not install_dependencies():
            return False
    
    # Copy codegraph.json to public directory if it exists
    codegraph_src = PROJECT_ROOT / "codegraph.json"
    public_dir = PROJECT_ROOT / "public"
    codegraph_dst = public_dir / "codegraph.json"
    
    if codegraph_src.exists():
        public_dir.mkdir(exist_ok=True)
        if not codegraph_dst.exists():
            shutil.copy2(codegraph_src, codegraph_dst)
            print(f"✅ Copied codegraph.json to {codegraph_dst}")
    
    # Start development server
    print("🌐 Starting development server at http://localhost:3000")
    print("Press Ctrl+C to stop the server")
    
    try:
        run_command("npm run dev")
    except KeyboardInterrupt:
        print("\n👋 Development server stopped.")
        return True

def build_frontend():
    """Build the frontend for production"""
    print("🏗️  Building SearchForge frontend for production...")
    
    if not check_node_installed():
        return False
    
    # Check if dependencies are installed
    node_modules = PROJECT_ROOT / "node_modules"
    if not node_modules.exists():
        print("📦 Installing dependencies first...")
        if not install_dependencies():
            return False
    
    # Build the project
    run_command("npm run build")
    
    # Copy codegraph.json to dist if it exists
    codegraph_src = PROJECT_ROOT / "codegraph.json"
    dist_dir = PROJECT_ROOT / "dist"
    codegraph_dst = dist_dir / "codegraph.json"
    
    if codegraph_src.exists() and dist_dir.exists():
        shutil.copy2(codegraph_src, codegraph_dst)
        print(f"✅ Copied codegraph.json to {codegraph_dst}")
    
    print("✅ Frontend built successfully!")
    print(f"📁 Build output: {dist_dir}")
    return True

def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python scripts/frontend.py <command>")
        print("Available commands:")
        print("  dev     - Start development server")
        print("  build   - Build for production")
        print("  install - Install dependencies")
        return
    
    command = sys.argv[1]
    
    if command == "dev":
        start_dev_server()
    elif command == "build":
        build_frontend()
    elif command == "install":
        install_dependencies()
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()

