"""
打包 Publime 为 EXE 文件（使用 Python 3.13 + PyInstaller）。
"""

import PyInstaller.__main__
import os
import sys
import tempfile

icon_path = os.path.join("ui", "sekiro_2_256x256.ico")

if not os.path.exists(icon_path):
    print(f"错误：图标文件不存在: {icon_path}")
    sys.exit(1)

# Windows Store 版 Python 3.13 不能在项目目录下写 build 文件，用临时目录
build_dir = os.path.join(tempfile.gettempdir(), "publime_build")

print(f"Python: {sys.version}")
print(f"Build dir: {build_dir}")
print(f"Icon: {icon_path}")

args = [
    "main.py",
    "--name=Publime",
    "--windowed",
    f"--icon={icon_path}",
    "--onefile",
    "--noupx",
    "--noconfirm",
    "--hidden-import=pymysql",
    "--collect-all=pymysql",
    f"--add-data={icon_path};ui",
    f"--workpath={build_dir}",
    "--distpath=dist",
]

try:
    PyInstaller.__main__.run(args)
    print("\nOK 打包完成！EXE 文件位于 dist/Publime.exe")
except Exception as e:
    print(f"\nFAIL 打包失败: {e}")
    sys.exit(1)
