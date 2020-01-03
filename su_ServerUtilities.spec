# -*- mode: python -*-

block_cipher = None


a = Analysis(['D:\\PycharmProjects\\Python2Project\\tools\\ServerUltilities\\su_ServerUtilities.py'],
             pathex=['D:\\PycharmProjects\\Python2Project\\tools\\ServerUltilities'],
             binaries=[],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='su_ServerUtilities',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False , icon='D:\\PycharmProjects\\Python2Project\\tools\\ServerUltilities\\ooopic_1569555377.ico')
