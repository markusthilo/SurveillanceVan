#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from pathlib import Path
from datetime import datetime
from zipfile import ZipFile, ZIP_DEFLATED

class Logger:
	'Advanced logging functionality'

	def __init__(self, level='info', dir=None, stem='log', path=None):
		'''Define logging by given level and to given file'''
		self.level = {
				'debug': logging.DEBUG,
				'info': logging.INFO,
				'warning': logging.WARNING,
				'error': logging.ERROR,
				'critical': logging.CRITICAL
			}[level]
		if path:
			self.dir = path.parent
			self.stem = path.stem
			self.path = path
		else:
			self.stem = stem
			if dir:
				self.dir = dir
			else:
				self.dir = Path().cwd()
			self.path = self.dir.joinpath(self.stem).with_suffix('.txt')
		self._start()
	
	def _start(self):
		'''Create logfile and start logging'''
		if self.path.is_file():
			zip_name = self.stem + datetime.now().strftime('_%Y-%m-%d_%H%M%S.zip')
			with ZipFile(self.dir / zip_name, 'w', ZIP_DEFLATED) as zf:
				zf.write(self.path, self.path.name)
			self.path.unlink()
		elif self.path.exists():
			raise RuntimeError(f'Unable to create log file {self.path}')
		logging.basicConfig(
			level = self.level,
			filename = self.path,
			format = '%(asctime)s %(levelname)s: %(message)s',
			datefmt = '%Y-%m-%d %H:%M:%S'
		)
		logging.debug(f'Start logging to {self.path}')

	def rotate(self):
		'''Rotate and backup old logfile as zip'''
		logging.shutdown()
		self._start()