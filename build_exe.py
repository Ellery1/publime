"""
打包 Publime 为 EXE 文件
"""

import PyInstaller.__main__
import os
import sys

# 获取图标路径
icon_path = os.path.join('ui', 'sekiro.icon')

# 检查图标文件是否存在
if not os.path.exists(icon_path):
    print(f"错误：图标文件不存在: {icon_path}")
    sys.exit(1)

print("开始打包 Publime...")
print(f"使用图标: {icon_path}")

# PyInstaller 参数
args = [
    'main.py',                          # 主程序文件
    '--name=Publime',                   # 程序名称
    '--windowed',                       # 不显示控制台窗口
    f'--icon={icon_path}',              # 程序图标
    '--onefile',                        # 打包成单个文件
    '--clean',                          # 清理临时文件
    '--noconfirm',                      # 不询问确认
    # 添加数据文件（Windows 使用分号）
    f'--add-data={icon_path};ui',       # 包含图标文件
    # 隐藏导入
    '--hidden-import=PySide6.QtCore',
    '--hidden-import=PySide6.QtGui',
    '--hidden-import=PySide6.QtWidgets',
]

print(f"PyInstaller 参数: {' '.join(args)}")

try:
    PyInstaller.__main__.run(args)
    print("\n✅ 打包完成！EXE 文件位于 dist/Publime.exe")
except Exception as e:
    print(f"\n❌ 打包失败: {e}")
    sys.exit(1)
