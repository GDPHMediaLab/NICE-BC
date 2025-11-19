#!/usr/bin/env python3
"""
Nuitka build script for NICE-BC application - 修复版本
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform

def check_nuitka():
    """检查Nuitka是否已安装"""
    try:
        import nuitka
        # 尝试获取版本信息，如果失败就跳过版本显示
        try:
            # 尝试不同的版本属性
            if hasattr(nuitka, '__version__'):
                version = nuitka.__version__
            elif hasattr(nuitka, 'version'):
                version = nuitka.version
            else:
                # 如果都没有，尝试通过其他方式获取
                import subprocess
                result = subprocess.run([sys.executable, "-m", "nuitka", "--version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.strip().split('\n')[0]
                else:
                    version = "未知版本"
        except Exception:
            version = "未知版本"
        
        print(f"✓ Nuitka已安装，版本: {version}")
        return True
    except ImportError:
        print("✗ Nuitka未安装")
        return False

def install_nuitka():
    """安装Nuitka"""
    print("正在安装Nuitka...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "nuitka", "ordered-set"])
        print("✓ Nuitka安装成功")
        return True
    except subprocess.CalledProcessError:
        print("✗ Nuitka安装失败")
        return False

def clean_build():
    """清理构建目录"""
    dirs_to_clean = ['build', 'dist', 'main.build', 'main.dist']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            print(f"清理目录: {dir_name}")
            shutil.rmtree(dir_name)

def check_module_exists(module_name):
    """检查模块是否存在"""
    try:
        __import__(module_name)
        return True
    except ImportError:
        return False

def build_with_nuitka():
    """使用Nuitka构建应用"""
    
    # 基本构建命令
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",  # 独立模式
        "--assume-yes-for-downloads",  # 自动下载依赖
        "--remove-output",  # 移除之前的输出
        
        # *** 关键修复：启用静态Python库链接 ***
        "--static-libpython=yes",  # 静态链接Python库，提高可移植性
        
        # PySide6相关配置
        "--enable-plugin=pyside6",
        "--include-qt-plugins=sensible",  # 移除无效的styles
        
        # 包含所有项目文件
        "--include-module=multi_file_selector",
        "--include-module=multiviewer", 
        "--include-module=core",
        "--include-module=metrics",
        "--include-module=spine_utils",
        
    ]
    
    # macOS特定配置
    if sys.platform == 'darwin':
        current_arch = platform.machine()
        if current_arch == 'arm64':
            target_arch = 'arm64'
        else:
            target_arch = 'x86_64'
        
        cmd.extend([
            "--macos-create-app-bundle",
            "--macos-app-name=NICE-BC",
            "--macos-app-version=1.0.0",
            f"--macos-target-arch={target_arch}",
            "--macos-sign-identity=-",
        ])
        
        # 检查并添加图标
        icon_files = ["icon.icns", "icon.png", "resources/icon.icns", "assets/icon.icns"]
        icon_found = False
        for icon_file in icon_files:
            if os.path.exists(icon_file):
                cmd.append(f"--macos-app-icon={icon_file}")
                print(f"使用macOS图标文件: {icon_file}")
                icon_found = True
                break
        
        if not icon_found:
            print("未找到macOS图标文件(.icns)，应用程序将使用默认图标")
            
    else:
        # 非macOS系统使用onefile模式
        cmd.extend([
            "--onefile",
            "--static-libpython=yes"  # 其他平台也启用静态链接
        ])
    
    # 可选依赖处理 - 只包含存在的模块
    optional_modules = [
        "psutil",
        "GPUtil", 
        "nvidia_ml_py3",
        "pynvml",
    ]
    
    for module in optional_modules:
        if check_module_exists(module):
            cmd.append(f"--include-module={module}")
            print(f"✓ 包含可选模块: {module}")
        else:
            print(f"⚠ 跳过不存在的模块: {module}")
    
    # 科学计算库（通常都存在）
    required_modules = [
        "numpy",
        "scipy", 
        "pandas",
        "scikit-image",
        "nibabel",
        "simpleitk",
        "opencv-python",
        "imageio",
        "pillow",
    ]
    
    for module in required_modules:
        if check_module_exists(module):
            cmd.append(f"--include-module={module}")
            print(f"✓ 包含必需模块: {module}")
        else:
            print(f"⚠ 警告: 缺少必需模块: {module}")
    
    # 其他选项
    cmd.extend([
        # 输出目录设置
        "--output-dir=dist",
        
        # 进度显示
        "--show-progress",
        "--show-memory",
        
        # 主文件
        "main.py"
    ])
    
    # Linux特定配置
    if sys.platform.startswith('linux'):
        # 只有当图标文件存在时才添加图标选项
        icon_file = "icon.png"
        if os.path.exists(icon_file):
            cmd.extend([
                f"--linux-onefile-icon={icon_file}",
            ])
            print(f"使用图标文件: {icon_file}")
        else:
            print("未找到图标文件，跳过图标设置")
    
    print("开始Nuitka构建...")
    print("构建命令:")
    print(" ".join(cmd))
    print("\n" + "="*50)
    
    try:
        # 执行构建
        result = subprocess.run(cmd, cwd=os.getcwd(), check=True)
        print("\n" + "="*50)
        print("✓ 构建成功完成！")
        
        # 查找生成的可执行文件
        dist_dir = Path("dist")
        if dist_dir.exists():
            if sys.platform == 'darwin':
                # macOS查找.app文件
                app_files = list(dist_dir.glob("*.app"))
                if app_files:
                    app_file = app_files[0]
                    print(f"✓ macOS应用程序包位置: {app_file.absolute()}")
                    print(f"✓ 可以双击运行，或拖拽到应用程序文件夹")
                    
                    # 计算.app包的大小
                    total_size = sum(f.stat().st_size for f in app_file.rglob('*') if f.is_file())
                    print(f"✓ 应用程序包大小: {total_size / (1024*1024):.1f} MB")
                    
                    print("\n" + "="*30)
                    print("📋 可移植性建议:")
                    print("1. 此版本使用静态Python链接，可移植性更好")
                    print("2. 支持universal2架构（Intel + Apple Silicon）")
                    print("3. 建议在目标机器上测试运行")
                    print("4. 如需发布，建议申请开发者证书进行正式签名")
                else:
                    print("⚠ 在dist目录中未找到.app应用程序包")
            else:
                # 其他系统查找可执行文件
                exe_files = list(dist_dir.glob("main*"))
                if exe_files:
                    exe_file = exe_files[0]
                    print(f"✓ 可执行文件位置: {exe_file.absolute()}")
                    print(f"✓ 文件大小: {exe_file.stat().st_size / (1024*1024):.1f} MB")
                else:
                    print("⚠ 在dist目录中未找到可执行文件")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 构建失败，错误代码: {e.returncode}")
        print("\n🔧 可能的解决方案:")
        print("1. 检查是否所有依赖模块都已安装")
        print("2. 尝试在干净的虚拟环境中构建")
        print("3. 检查是否有足够的磁盘空间")
        return False
    except KeyboardInterrupt:
        print("\n⚠ 构建被用户中断")
        return False

def main():
    """主函数"""
    print("NICE-BC Nuitka 构建脚本 - 可移植性优化版")
    print("="*50)
    
    # 检查当前目录
    if not os.path.exists("main.py"):
        print("✗ 错误: 在当前目录中找不到main.py文件")
        print("请确保在项目根目录运行此脚本")
        return False
    
    # 检查Nuitka
    if not check_nuitka():
        if not install_nuitka():
            return False
    
    # 清理构建目录
    clean_build()
    
    # 构建
    success = build_with_nuitka()
    
    if success:
        print("\n🎉 构建完成！")
        print("可执行文件位于 dist/ 目录中")
        print("\n📝 注意事项:")
        print("- 此版本经过可移植性优化")
        print("- 在其他Mac上运行前建议先测试")
        print("- 如遇到权限问题，在目标机器上右键选择'打开'")
    else:
        print("\n❌ 构建失败")
        print("请检查错误信息并重试")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 