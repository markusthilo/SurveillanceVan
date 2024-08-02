#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2024-08-02'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Watch copy processes'

### Standard libs ###
import logging
from pathlib import Path
from filecmp import cmp as filecmp
from threading import Thread
from time import sleep
from datetime import datetime
from argparse import ArgumentParser
### Custom libs ###
from lib.pathutils import PathUtils
from lib.configreader import ConfigReader
from lib.advancedlogger import Logger

class TreeCmp:
	'''Compare recursivly and check what is in minor but missing in major'''

	def __init__(self, major_root, minor_root):
		'''Generate attributes "missing" = dict'''
		self.missing = list()
		for minor_path, rel_path, tp in PathUtils.walk(minor_root):
			major_path = major_root / rel_path
			if tp == 'file':
				if not major_path.is_file():
					self.missing.append((rel_path, 'missing file'))
				elif not filecmp(major_path, minor_path):
					self.missing.append((rel_path, 'divergent file'))
			elif tp == 'dir' and not major_path.is_dir():
				self.missing.append((rel_path, 'missing dir'))

class Trigger:
	'''Surveillance of trigger directory'''

	def __init__(self, root_path):
		'''Generate object'''
		self.root_path = root_path
		self.existing_dirs = PathUtils.get_subdirs(self.root_path)

	def get_new_dirs(self):
		'''Returns set with new subdirectory paths'''
		#for dir in self.existing_dirs - PathUtils.get_subdirs(self.root_path):
		for dir in self.existing_dirs:	# debug
			if dir.joinpath(config.trigger_filename).is_file():
				
				yield dir

class Check:
	'''Run check'''

	def __init__(self, config):
		'''Build object'''
		logging.info(f'Checking what is missing in {config.work_dir} and {config.backup_dir}')
		trigger = Trigger(config.trigger_dir)
		for dir in trigger.get_new_dirs():
			print(dir)

		'''
		tc = TreeCmp(config.work_path, config.backup_path)
		if len(tc.missing) == 0:
			logging.info('Nothing is missing')
		else:
			msg = f'{len(tc.missing)} missing path(s):'
			for path, tp in tc.missing:
				msg += f'\n\t{tp}:\t{path}'
			logging.info(msg)
		'''

class MainLoop:
	'Main loop'

	def __init__(self, config):
		'Initiate main loop'
		self.config = config
		logging.info('Starting main loop')
		while True:	# check if time matches
			if datetime.now().strftime('%H:%M') in config.updates:
				self.worker()
				sleep(config.sleep)

	def worker(self):
		'Do the main work'
		try:
			Check(config)
		except Exception as err:
			logging.error(err)

if __name__ == '__main__':	# start here if called as application
	__path__ = Path(__file__)
	argparser = ArgumentParser(description=__description__)
	argparser.add_argument('-c', '--config', type=Path, default=__path__.with_suffix('.conf'),
		help='Config file', metavar='FILE')
	argparser.add_argument('-d', '--debug', default=False, action='store_true',
		help='Debug mode, ignore -l/--level')
	argparser.add_argument('-f', '--logfile', type=Path,
		help='Log file', metavar='FILE')
	argparser.add_argument('-l', '--loglevel', choices=('debug', 'info', 'warning', 'error', 'critical'),
		help='Log level, ignorde on -d/--debug', metavar='STRING')
	args = argparser.parse_args()
	config = ConfigReader(args.config)
	if args.debug:
		log_level = 'debug'
	elif args.loglevel:
		log_level = args.loglevel
	else:
		log_level = config.log_level
	if args.logfile:
		log_path = args.logfile
	else:
		log_path = config.log_file
	Logger(log_path, log_level)
	if log_level == 'debug':
		logging.debug('Check on debug level')
		Check(config)
		#print(log_path.read_text())
	else:
		MainLoop(config)
