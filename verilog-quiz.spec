# -*- mode: python ; coding: utf-8 -*-
# PyInstaller onedir 打包配置（v2：纯标准库后端 + 静态前端）
# 构建：uv run pyinstaller verilog-quiz.spec --noconfirm

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('webui', 'webui')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='verilog-quiz-system',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,          # windowed：无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='verilog-quiz-system',
)
