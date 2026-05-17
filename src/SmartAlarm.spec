# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

# Collecting the missing runtime dependencies natively inside the spec
ctk_datas, ctk_binaries, ctk_hiddenimports = collect_all('customtkinter')
tk_datas, tk_binaries, tk_hiddenimports = collect_all('tkinter')
np_datas, np_binaries, np_hiddenimports = collect_all('numpy')

current_dir = os.path.abspath('.')

a = Analysis(
    ['app_shrunk.py'],
    pathex=[current_dir],
    binaries=[('/Users/tuhi-macos/miniconda3/envs/smart_alarm_env/lib/libsndfile.dylib', '.')] + ctk_binaries + tk_binaries,
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
        'torch', 'torchaudio', 'torchvision', 'pandas', 'matplotlib', 'pygame',
    ],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,     # Natively include binaries in the execution runtime
    a.zipfiles,     # Natively include zipfiles in the execution runtime
    a.datas,        # Natively include datas in the execution runtime
    name='TheSmartAlarmV2',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=False,
    console=True,   # Kept True so we can monitor errors directly from the terminal
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

app = BUNDLE(
    exe,
    name='TheSmartAlarmV2.app',
    icon='icon.icns',
    bundle_identifier='com.toshan.smartalarm',
    info_plist={
        'NSMicrophoneUsageDescription': 'Smart Alarm needs microphone access to monitor room acoustics and detect sleep cycles.',
    },
)