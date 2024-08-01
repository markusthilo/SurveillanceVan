#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

class Logger:
	'Logging for this tool'

	def __init__(self, path, level):
		'Initiate logging by given level and to given file'
		logging.basicConfig(
			level={
				'debug': logging.DEBUG,
				'info': logging.INFO,
				'warning': logging.WARNING,
				'error': logging.ERROR,
				'critical': logging.CRITICAL
			}[level],
			filename = path,
			format = '%(asctime)s %(levelname)s: %(message)s',
			datefmt = '%Y-%m-%d %H:%M:%S'
		)
		logging.debug(f'Start logging to {path}')
