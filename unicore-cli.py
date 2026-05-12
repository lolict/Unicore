#!/usr/bin/env python3
"""
UniCore - 通用核心平台命令行工具
===================================
统一的命令行界面，整合所有功能。
"""

import sys
import os
import json
import argparse
from pathlib import Path


def print_banner():
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    UniCore - 通用核心平台                    ║
║                  Unified Core Platform v2.0                  ║
╚══════════════════════════════════════════════════════════════╝
    """)


def init_project(args):
    """初始化项目"""
    print("📦 初始化 UniCore 项目...")
    
    root = Path(args.path or ".")
    src = root / "src"
    core = src / "core"
    cloud = src / "cloud"
    
    for p in [core / "isa", core / "vm", 
              cloud / "gist", cloud / "webdav", cloud / "p2p", cloud / "sync"]:
        p.mkdir(parents=True, exist_ok=True)
    
    print("✅ 项目结构创建完成！")


def show_architecture(args):
    """显示架构支持"""
    print("📋 支持的架构：")
    print("  ✅ x86/x64")
    print("  ✅ ARMv7+")
    print("  ✅ RISC-V (RV32/64)")
    print("  ✅ MIPS")
    print("\n  🔄 自动检测并翻译")


def configure_cloud(args):
    """配置云端同步"""
    print("🔧 配置云端同步...")
    
    config = {}
    
    use_gist = input("  是否使用 GitHub Gist? (y/n): ").lower() == "y"
    if use_gist:
        config["github_token"] = input("  GitHub Token: ")
        config["github_username"] = input("  GitHub 用户名: ")
    
    use_webdav = input("  是否使用 WebDAV/坚果云? (y/n): ").lower() == "y"
    if use_webdav:
        config["webdav"] = {
            "host": input("  WebDAV 服务器地址: "),
            "username": input("  用户名: "),
            "password": input("  密码: ")
        }
    
    config_file = "unicore_config.json"
    with open(config_file, "w") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 配置已保存到 {config_file}")


def run_demo(args):
    """运行演示"""
    print("🚀 运行 UniCore 演示...")
    
    print("  1. 初始化虚拟机")
    print("  2. 加载测试程序")
    print("  3. 执行指令")
    print("  4. 显示结果")
    
    print("\n✅ 演示完成！")


def main():
    parser = argparse.ArgumentParser(description="UniCore - 通用核心平台命令行工具")
    subparsers = parser.add_subparsers(title="命令")
    
    # init
    parser_init = subparsers.add_parser("init", help="初始化项目")
    parser_init.add_argument("-p", "--path", help="项目路径")
    parser_init.set_defaults(func=init_project)
    
    # arch
    parser_arch = subparsers.add_parser("arch", help="显示架构支持")
    parser_arch.set_defaults(func=show_architecture)
    
    # config
    parser_config = subparsers.add_parser("config", help="配置云端同步")
    parser_config.set_defaults(func=configure_cloud)
    
    # demo
    parser_demo = subparsers.add_parser("demo", help="运行演示")
    parser_demo.set_defaults(func=run_demo)
    
    args = parser.parse_args()
    
    print_banner()
    
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
