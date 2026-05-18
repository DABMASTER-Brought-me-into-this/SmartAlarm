# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all

# Collecting the missing runtime dependencies
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')
tk_datas, tk_binaries, tk_hiddenimports = collect_all('tkinter')
np_datas, np_binaries, np_hiddenimports = collect_all('numpy')

current_dir = os.path.abspath('.')

# DYNAMIC OS CHECK: Only inject the Mac audio library if building on macOS
custom_binaries = []
if sys.platform == 'darwin':
    custom_binaries = [('/Users/tuhi-macos/miniconda3/envs/smart_alarm_env/lib/libsndfile.dylib', '.')]
elif sys.platform == 'win32':
    # On Windows, we ensure we collect the runtime DLLs if they exist in the environment
    pass

a = Analysis(
    ['app_shrunk.py'],
    pathex=[current_dir],
    binaries=custom_binaries + ctk_binaries + tk_binaries,
    datas=[
        ('OriginalWeightMetrics.npz', '.'),
        ('sheback.wav', '.'),
        ('Scalers', 'Scalers'),
    ] + ctk_datas + tk_datas + np_datas,
    hiddenimports=[
        'sounddevice',
        'just_playback',
        'custom',
        'logic_shrunk',
        'neuralnetwork_shrunk',
    ] + ctk_hiddenimports + tk_hiddenimports + np_hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'torch', 'torchaudio', 'torchvision', 'pandas', 'matplotlib', 'pygame', 'sqlite3',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='TheSmartAlarmV2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=True,
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
    strip=True,
    upx=False,
    upx_exclude=[],
    name='TheSmartAlarmV2',
)

if sys.platform == 'darwin':
    app = BUNDLE(
        coll,
        name='TheSmartAlarmV2.app',
        icon='icon.icns',
        bundle_identifier='com.toshan.smartalarm',
        info_plist={
            'NSMicrophoneUsageDescription': 'Smart Alarm needs microphone access to monitor room acoustics and detect sleep cycles.',
        },
    )