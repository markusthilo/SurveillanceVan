#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED

class PathUtils:
	'''Some functions for pathlib's Path class'''

	BLOCK_SIZE = sha256().block_size * 1024

	@staticmethod
	def walk(root):
		'''Recursivly give all sub-paths'''
		for path in root.rglob('*'):
			if path.is_file():
				tp = 'file'
			elif path.is_dir():
				tp = 'dir'
			else:
				tp = None
			yield path, path.relative_to(root), tp

	@staticmethod
	def tree(root):
		'''Get size'''
		dirs = {Path('.'): {'depth': 0, 'size': 0, 'files': 0}}
		files = dict()
		for path in root.rglob('*'):
			rel_path = path.relative_to(root)
			rel_depth = len(list(rel_path.parents))
			if path.is_dir():
				dirs[rel_path] = {'depth': rel_depth, 'size': 0, 'files': 0}
			elif path.is_file():
				size = path.stat().st_size
				files[rel_path] = {'depth': rel_depth, 'size': size}
				for parent in rel_path.parents:
					dirs[parent]['size'] += size
					dirs[parent]['files'] += 1
		return dirs, files

	@staticmethod
	def hash_file(path):
		'''Calculate SHA256 from file (pathlib.Path)'''
		hash = sha256()
		with path.open('rb') as fh:
			while True:
				block = fh.read(self.BLOCK_SIZE)
				if not block:
					break
				hash.update(block)
		return hash.hexdigest()

	@staticmethod
	def copy_file(self, src, dst):
		'''Copy one file and calculate hashes (src + dst have to be pathlib.Path of file)'''
		hash = sha256()
		with src.open('rb') as sfh, dst.open('wb') as dfh:
			while True:
				block = sfh.read(self.BLOCK_SIZE)
				if not block:
					break
				dfh.write(block)
				hash.update(block)
		return hash.hexdigest()

	@staticmethod
	def zip_dir(self, root, zip_path):
		'''Build zip file'''
		zip_path = zip_path.with_suffix('.zip')
		file_error_cnt = 0
		dir_error_cnt = 0
		with ZipFile(zip_path, 'w', ZIP_DEFLATED) as zf:
			for path, relative, tp in PathUtils.walk(self.root_path):
				if tp == 'File':
					try:
						zf.write(path, relative)
					except:
						file_error_cnt += 1
				elif tp == 'Dir':
					try:
						zf.mkdir(f'{relative}')
					except:
						dir_error_cnt += 1
		return zip_path, file_error_cnt, dir_error_cnt


