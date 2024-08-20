#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-08-20'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Watch copy processes'

### Standard libs ###
import logging
from pathlib import Path
from zipfile import ZipFile
#from threading import Thread
from time import sleep
from datetime import datetime
from argparse import ArgumentParser
### Custom libs ###
from lib.pathutils import PathUtils
from lib.stringutils import StringUtils
from lib.configreader import ConfigReader
from lib.advancedlogger import Logger

"""
class Trigger:
	'''Surveillance of trigger directory'''

	def __init__(self, root_path):
		'''Generate object'''
		self.root_path = root_path
		self.existing_dirs = PathUtils.get_subdirs(self.root_path)

	def get_new_dirs(self):
		'''Returns set with new subdirectory paths'''
		#for dir in self.existing_dirs - PathUtils.get_subdirs(self.root_path):
		for dir_path in self.existing_dirs:	# debug
			tsv_path = dir_path.joinpath(config.trigger_filename)
			if tsv_path.is_file():
				hashes = dict()
				for line in tsv_path.read_text().split('\n')[1:]:
					entries = line.split('\t')
					hashes[Path(entries[0])] = entries[2]
				yield dir_path.relative_to(self.root_path), hashes
"""

class Trigger:
	'''Surveillance of trigger directory'''

	def __init__(self, config):
		'''Get trigger directories from config file'''
		self._root_dirs = [	# build list of trigger subpaths
			config.trigger_dir/(subdir.strip())
			for subdir in config.trigger_subdirs.split(',')
		]
		logging.debug(f'Surveilling {StringUtils.join(self._root_dirs, delimiter=", ")}')
		
	def read(self):
		'''Read trigger directory, return relative path, file size and hash from tsv file'''
		for dep_path in self._root_dirs:	# loop departments
			if not dep_path.is_dir():	# skip if dir does not exist
				logging.warning(f'Did not find {dep_path}')
				continue
			logging.debug(f'Reading structure of {dep_path}')
			for dir_path in PathUtils.get_subdirs(dep_path):	# loop case dirs
				tsv_path = dir_path.joinpath(config.trigger_filename)
				if tsv_path.is_file():	# check if tsv file with sizes and hashes exists
					sizes = dict()	# dict with file sizes to generate from tsv file
					hashes = dict()	# dict with file hashes to generate from tsv file
					for line in tsv_path.read_text().split('\n')[1:]:	# read tsv file
						entries = line.split('\t')
						sizes[Path(entries[0])] = int(entries[1])
						hashes[Path(entries[0])] = entries[2]
					yield dir_path.relative_to(dep_path), sizes, hashes

class Directory:
	'''Directory to surveil'''

	def __init__(self, path):
		'''Set directory path'''
		self.path = path

	def check(self, sizes, hashes):
		'''Check if files exists, file sizes and hashes are matching'''
		logging.debug(f'Checking {self.path} for new entries/directories')
		self.files = {	# all (recursivly) file paths in the directory
			path for path in self.path.rglob('*')
			if path.is_file()
		}
		warning_cnt = 0
		for rel_path in sizes:	# loop given files (sizes+hashes) and check for mismatches in directory
			abs_path = self.path/rel_path
			if not abs_path in self.files:
				logging.warning(f'Did not find {rel_path} in {self.path}')
				warning_cnt += 1
			elif abs_path.stat().st_size != sizes[rel_path]:
				logging.warning(f'Mismatching file size of {abs_path}')
				warning_cnt += 1
			elif PathUtils.hash_file(abs_path) != hashes[rel_path]:
				logging.warning(f'Mismatching hash value of {abs_path}')
				warning_cnt += 1
		return warning_cnt	# return number of warnings / mismatching files

class Archive:
	'''Zip archive to surveil'''

	def __init__(self, path):
		'''Open archive to read'''
		self.path = path
		self._zipfile = ZipFile(self.path)

	def check(self, sizes, hashes):
		'''Check if files exists, file sizes and hashes are matching'''
		dir_path = Path(self.path.stem)
		self.members = {	# all (recursivly) members with file sizes of the zip archive
			Path(member.filename): member.file_size for member in self._zipfile.infolist()
		}
		warning_cnt = 0
		for rel_path in sizes:	# loop given files (sizes+hashes) and check for mismatches in directory
			in_zip_path = dir_path/rel_path
			if not in_zip_path in self.members:
				logging.warning(f'Did not find {in_zip_path} in {self.path}')
				warning_cnt += 1
			elif self.members[in_zip_path] != sizes[rel_path]:
				logging.warning(f'Mismatching file size of {in_zip_path} in {self.path}')
				warning_cnt += 1
			else:
				if PathUtils.hash_zip(self._zipfile, in_zip_path) != hashes[rel_path]:
					logging.warning(f'Mismatching hash value of {in_zip_path} in {self.path}')
					warning_cnt += 1
		return warning_cnt	# return number of warnings / mismatching files

class Check:
	'''Run check'''

	def __init__(self, config):
		'''Build object'''
		self.trigger = Trigger(config)

	def check(self):
		'''Run check'''
		new_cnt = 0
		warning_cnt = 0
		for rel_path, sizes, hashes in self.trigger.read():
			new_cnt += 1
			sub_dir = rel_path.name[:2]
			work_dir = Directory(config.work_dir/sub_dir/rel_path)
			backup_dir = Directory(config.backup_dir/sub_dir/rel_path)
			warning_cnt += work_dir.check(sizes, hashes) + backup_dir.check(sizes, hashes)
			#backup_zip = Archive(config.backup_dir/sub_dir/rel_path.with_suffix('.zip'))
			#warning_cnt = work_dir.check(sizes, hashes) + backup_zip.check(sizes, hashes)
		msg = 'Check finished. '
		if new_cnt == 0:
			msg += 'Did not find new directories.'
		elif warning_cnt == 0:
			msg += f'All files were copied to {config.work_dir} and {config.backup_dir}'
		else:
			msg += f'{warning_cnt} problem(s) occured.'
			print(msg)
		logging.info(msg)

class MainLoop:
	'Main loop'

	def __init__(self, config, log):
		'Initiate main loop'
		self.checker = Check(config)
		logging.info('Starting main loop')
		while True:	# check if time matches
			if datetime.now().strftime('%H:%M') in config.updates:
				self.worker()
				sleep(config.sleep)

	def worker(self):
		'Do the main work'
		try:
			self.checker.check()
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
	if args.debug:	# log level given on cmd line beats config file
		log_level = 'debug'
	elif args.loglevel:
		log_level = args.loglevel
	else:
		log_level = config.log_level
	log = Logger(level=log_level, dir=config.log_dir, stem=config.log_stem, path=args.logfile)
	if log_level == 'debug':
		logging.debug('Check on debug level')
		Check(config).check()
		print(log.path.read_text())
	else:
		MainLoop(config, log)
