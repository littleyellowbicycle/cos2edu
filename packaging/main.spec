# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('static', 'static'),
    ],
    hiddenimports=[
        'sqlalchemy.sql.default_comparator',
        'aiosqlite',
        'uvicorn',
        'starlette',
        'starlette.staticfiles',
        'starlette.responses',
        'fastapi',
        'pydantic',
        'pydantic_settings',
        'slowapi',
        'slowapi.errors',
        'httpx',
        'jinja2',
        'python_multipart',
        'jiter',
        'anyio',
        'sniffio',
        'idna',
        'h11',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[
        'numpy',
        'pandas',
        'matplotlib',
        'tkinter',
        'test',
        'tests',
        'pytest',
        'scipy',
        'PIL',
        'cv2',
    ],
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='cos2edu',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='cos2edu',
)