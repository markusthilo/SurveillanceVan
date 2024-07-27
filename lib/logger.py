#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from datetime import datetime

class Logger:
	'''Simple logging'''

	def __init__(self, path, info=None, echo=print):
		'''Open/create directory to write logs'''
		self._fh = path.open(mode='w', buffering=1, encoding='utf-8')
		self._echo = echo
		self.warnings = 0
		self.errors = 0
		if info:
			self.info(info)

	def _now(self):
		'''Return timestamp'''
		return datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

	def info(self, *args):
		'''Print info to log'''
		print(self._now(), 'INFO', *args, file=self._fh)
		self._echo(*args)

	def warning(self, *args):
		'''Print warning to log'''
		print(self._now(), 'WARNING', *args, file=self._fh)
		self._echo('WARNING', *args)
		self.warnings += 1

	def error(self, *args):
		'''Print error to log'''
		print(self._now(), 'ERROR', *args, file=self._fh)
		self._echo('ERROR', *args)
		self.errors += 1

	def close(self):
		'''Close logfile'''
		self._fh.close()
		return self.warnings + self.warnings > 0
