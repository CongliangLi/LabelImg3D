# -*- mode: python ; coding: utf-8 -*-


block_cipher = None
py_files = [
    "libs\\actor_manager.py",
    "libs\\common.py",
    "libs\\dataset.py",
    "libs\\kitti_util.py",
    "libs\\lcamera_property.py",
    "libs\\lKITTI_2_LabelImg3d.py",
    "libs\\qjsonmodel.py",
    "libs\\sconfig.py",
    "libs\\simagelist.py",
    "libs\\slabel3dannotation.py",
    "libs\\slabelimage.py",
    "libs\\slog.py",
    "libs\\smodellist.py",
    "libs\\sproperty.py",
    "libs\\test.py",
    "libs\\test_pyqtconfig.py",
    "libs\\test1.py",
    "libs\\Ui_main.py",
    "libs\\Ui_test.py",
    "libs\\utils.py",
    "libs\\pyqtconfig\\config.py",
    "libs\\pyqtconfig\\demo.py",
    "libs\\pyqtconfig\\qt.py"

]

add_files = [
    ("libs/main.ui", "."),
    ("libs/icons/*.ico", "icons")
]


a = Analysis(py_files,
             pathex=['F:\\my_desktop\\PycharmFiles\\3D_detection\\labelimg3d'],
             binaries=[],
             datas=add_files,
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
          name='labelImg3d',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
          icon='.\\libs\\icons\\icon.ico')

