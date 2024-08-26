#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-08-26'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Use PyInstaller to build SlowCopy executables'

from pathlib import Path
from shutil import rmtree
import PyInstaller.__main__

if __name__ == '__main__':	# start here
	cwd_path = Path.cwd()
	icon_path = cwd_path / 'appicon.ico'
	build_path = cwd_path / 'build'
	build_path.mkdir(exist_ok=True)
	for user, dst, log in [
		('LKA 71', 'C:/Users/THI/Documents/test_dst', 'C:/Users/THI/Documents/test_log'),
		('THI', 'C:/Users/THI/Documents/test_dst', 'C:/Users/THI/Documents/test_log')
	]:
		slowcopy_name = f'slowcopy-{user.lower().replace(' ', '_')}.py'
		slowcopy_path = build_path / slowcopy_name
		with slowcopy_path.open(mode='w', encoding='utf-8') as f:
			for line in cwd_path.joinpath('slowcopy.py').read_text(encoding='utf-8').split('\n'):
				if line.startswith('__description__ ='):
					print(f"__description__ = 'Distribution {user}'", file=f)
				elif line.startswith('__destination__ ='):
					print(f"__destination__ = '{dst}'", file=f)
				elif line.startswith('__logging__ ='):
					print(f"__logging__ = '{log}'", file=f)
				else:
					print(line, file=f)
		PyInstaller.__main__.run([f'{slowcopy_path}', '--onefile', '--icon', f'{icon_path}', '--noconsole'])
		cwd_path.joinpath(slowcopy_name).with_suffix('.spec').unlink()
	rmtree(build_path)
