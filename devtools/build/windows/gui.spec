# -*- mode: python -*-
# vim: ft=python

import os

block_cipher = None

dll_dir = 'C:\\Users\\Jooa\\.conda\\envs\\videotracker\\Library\\bin'
dlls = [
    os.path.join(dll_dir, dll) 
    for dll in os.listdir(dll_dir)
    if dll.startswith('opencv') and dll.endswith('.dll')
]

a = Analysis(['gui.py'],
             pathex=['C:\\Users\\Jooa\\Code\\videotracker'],
             binaries=[
                 (name, '.') for name in dlls
             ],
             datas=[],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='gui',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False)
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='gui')
