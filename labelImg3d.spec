# -*- mode: python ; coding: utf-8 -*-


block_cipher = None


a = Analysis(['labelImg3d.py'],
             pathex=['F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d'],
             binaries=[],
             datas=[("libs/*.ui", "libs"),("libs/utils/*.ui","libs/utils"),("libs/icons/*.ico", "libs/icons"),("libs/system_config.json", "libs")],
             hiddenimports=['vtkmodules','vtkmodules.all','vtkmodules.qt.QVTKRenderWindowInteractor','vtkmodules.util','vtkmodules.util.numpy_support','vtkmodules.numpy_interface','vtkmodules.numpy_adapter'],
             hookspath=["libs/hooks/"],
             hooksconfig={},
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
          a.binaries,
          a.zipfiles,
          a.datas,  
          [],
          name='labelImg3d',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=False,
          icon= './libs/icons/icon.ico',
          disable_windowed_traceback=False,
          target_arch=None,
          codesign_identity=None,
          entitlements_file=None )
