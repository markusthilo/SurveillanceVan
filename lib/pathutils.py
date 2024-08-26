#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED

class PathUtils:
	'''Some functions for pathlib's Path class'''

	BLOCK_SIZE = sha256().block_size * 1024

	@staticmethod
	def get_subdirs(root):
		'''Returns set with subdirectory paths, NOT recursivly'''
		return { path for path in root.iterdir() if path.is_dir() }

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
		'''Get size, subdirs and subfiles (recursivly)'''
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
		'''Calculate SHA256 from file'''
		sha = sha256()
		with path.open('rb') as fh:
			while True:
				block = fh.read(PathUtils.BLOCK_SIZE)
				if not block:
					break
				sha.update(block)
		return sha.hexdigest()

	@staticmethod
	def hash_zip(zipfile, path):
		'''Calculate SHA256 from file in ZIP archive'''
		sha = sha256()
		with zipfile.open(path.as_posix()) as fh:
			while True:
				block = fh.read(PathUtils.BLOCK_SIZE)
				if not block:
					break
				sha.update(block)
		return sha.hexdigest()

	@staticmethod
	def copy_file(src, dst):
		'''Copy one file and calculate shaes, return sha on success'''
		sha = sha256()
		with src.open('rb') as sfh, dst.open('wb') as dfh:
			while True:
				block = sfh.read(PathUtils.BLOCK_SIZE)
				if not block:
					break
				dfh.write(block)
				sha.update(block)
		src_sha = sha.hexdigest()
		if PathUtils.hash_file(dst) == src_sha:
			return src_sha

	@staticmethod
	def zip_dir(root, archive):
		'''Build zip file'''
		file_errors = list()
		dir_errors = list()
		with ZipFile(archive, 'w', ZIP_DEFLATED) as zf:
			for path, relative, tp in PathUtils.walk(root):
				if tp == 'file':
					try:
						zf.write(path, relative)
					except:
						file_errors.append(relative)
				elif tp == 'dir':
					try:
						zf.mkdir(f'{relative}')
					except:
						dir_errors.append(relative)
		return PathUtils.hash_file(archive), file_errors, dir_errors

