#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from hashlib import sha256
from zipfile import ZipFile, ZIP_DEFLATED
from filecmp import cmp as filecmp
from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM
from threading import Thread
from datetime import datetime

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
		dirs = dict()
		files = dict()
		for path in root.rglob('*'):
			rel_path = path.relative_to(root)
			rel_depth = len(list(rel_path.parents))
			if path.is_dir():
				dirs[rel_path] = {'depth': rel_depth, 'size': 0}
			elif path.is_file():
				size = path.stat().st_size
				files[rel_path] = {'depth': rel_depth, 'size': size}
				if rel_depth > 1:
					dirs[rel_path.parent]['size'] += size
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
	def zip_dir(self, root):
		'''Build zip file'''
		zip_path = root.with_suffix('.zip')
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

	@staticmethod
	def __init__(major_root, minor_root):
		'''Compare recursivly and check what is in minor but missing in major'''
		missing = list()
		for minor_path, rel_path, tp in PathUtils.walk(minor_root):
			major_path = major_root / rel_path
			if tp == 'file':
				if not major_path.is_file():
					missing.append((rel_path, 'missing file'))
				elif not filecmp(major_path, minor_path):
					missing.append((rel_path, 'divergent file'))
			elif tp == 'dir' and not major_path.is_dir():
				missing.append((rel_path, 'missing dir'))
		return missing
