#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2024-07-14'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Watch copy processes'

import logging
from pathlib import Path
from filecmp import cmpfiles
from sys import exit as sysexit
from re import match
from subprocess import Popen, PIPE, STDOUT
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from csv import DictReader, DictWriter
from csv import writer as SequenceWriter
from argparse import ArgumentParser

class Logger:
	'Logging for this tool'

	def __init__(self, path, level):
		'Initiate logging by given level and to given file'
		if not path:
			path = __path__.with_suffix('log')
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
		logging.info(f'Start logging to {path}')

class Config:
	'Handle the config file'

	def __init__(self, configfile):
		'Get configuration from file and initiate logging'
		config = ConfigParser()
		config.read(configfile)
		self.source_root = config['SOURCE']['root']
		

		
		'''
		self.fieldnames = [ fn.strip(' ') for fn in  config['FILELIST']['fieldnames'].split(',') ]
		self.pgp_cmd = Path(config['PGP']['command'])
		self.pgp_passphrase = config['PGP']['passphrase']
		self.triggerfile = Path(config['TRIGGER']['filepath'])
		self.updates = [ t.strip(' ') for t in config['TRIGGER']['time'].split(',') ]
		self.sleep = int(config['TRIGGER']['sleep'])
		if self.sleep < 60:	# or there will be several polls in one minute
			self.sleep = 60
		self.sourcetype = config['SOURCE']['type'].lower()
		self.sourcepath = Path(config['SOURCE']['path'])
		if self.sourcetype == 'url':
			self.sourcepath = config['SOURCE']['path']
			if self.sourcepath[-1] != '/':
				self.sourcepath += '/'
			self.xpath = config['SOURCE']['xpath']
			self.retries = int(config['SOURCE']['retries'])
			self.retrydelay = int(config['SOURCE']['delay'])
		else:
			self.sourcepath = Path(config['SOURCE']['path'])
			self.xpath = ''
		self.backuppath = Path(config['BACKUP']['path'])
		self.targets = dict()
		for section in config.sections():
			if section[:6] == 'TARGET':
				if section == 'TARGET':
					self.targetpath = Path(config['TARGET']['path'])
				else:
					self.targets[Path(config[section]['path'])] = config[section]['pattern']
		'''

class ExtPath:
	'''Add some methods to pathlib´s Path Class'''

	@staticmethod
	def path(arg):
		'''Generate Path object'''
		if isinstance(arg, str):
			return Path(arg.strip('"'))
		else:
			return Path(arg)

	@staticmethod
	def child(name, parent=None):
		'''Generate full path'''
		if not name and not parent:
			return Path.cwd()
		if parent:
			parent = Path(parent)
		else:
			parent = Path.cwd()
		if name:
			return parent/name
		else:
			return parent

	@staticmethod
	def mkdir(path):
		'''Create directory or just give full dorectory path if exists'''
		if not path:
			return Path.cwd()
		path = Path(path)
		path.mkdir(parents=True, exist_ok=True)
		return path

	@staticmethod
	def get_size(path):
		'''Get size'''
		if not path:
			path = Path.cwd()
		if path.is_dir():
			return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
		if path.is_file():
			return path.stat().st_size

	@staticmethod
	def mkfname(string):
		'''Eleminate chars that do not work in filenames'''
		string = normalize('NFKD', string).encode('ASCII', errors='ignore').decode('utf-8', errors='ignore').replace('/', '_')
		return ''.join(char for char in string if char in f'-_{ascii_letters}{digits}')

	@staticmethod
	def normalize(string):
		'''Normalize path given as string for better comparison'''
		return normalize('NFKD', string).strip('\\/').encode(errors='surrogateescape').decode(errors='surrogateescape')

	@staticmethod
	def normalize_posix(path):
		'''Normalize Posix path for better comparison'''
		return f'{path}'.strip('\t\n/').replace('\n', ' ').replace('\t', ' ').replace('\r', '').replace('/', '\\')

	@staticmethod
	def normalize_win(path):
		'''Normalize Windows path for better comparison'''
		return f'{path}'.strip('\t\n\\').replace('\n', ' ').replace('\t', ' ').replace('\r', '')

	@staticmethod
	def walk(root):
		'''Recursivly give all sub-paths'''
		for path in root.rglob('*'):
			if path.is_file():
				tp = 'File'
			elif path.is_dir():
				tp = 'Dir'
			else:
				tp = None
			yield path, path.relative_to(root), tp

	@staticmethod
	def quantitiy(root):
		'''Get quantitiy of all items'''
		return len(list(root.rglob('*')))

	@staticmethod
	def parented_walk(root):
		'''Walk throught file system str'''
		for path in root.rglob('*'):
			if path.is_dir():
				yield path, path.parent, path.name, 'dir'
			elif path.is_file():
				yield path, path.parent, path.name, 'file'
			else:
				yield path, path.parent, path.name, None

	@staticmethod
	def read_utf_head(path, lines_in=10, lines_out=1):
		'''Read first lines of TSV/text file while checking UTF encoding'''
		lines = list()
		last = max(lines_in, lines_out) - 1
		for codec in __utf__:
			try:
				with path.open('r', encoding=codec) as fh:
					for cnt, line in enumerate(fh):
						lines.append(line.strip())
						if cnt == last:
							break
					if lines_out == 1:
						return codec, lines[0]
					return codec, lines[:lines_out]
			except UnicodeError:
				continue
		raise RuntimeError('Unable to detect UTF codec')

	@staticmethod
	def read_bin(path, offset=0, lines=64, bytes_per_line=16):
		'''Genereate string from binary file'''
		string = ''
		with path.open('rb') as fh:
			for line_offset in range(offset, offset+lines):
				string += f'{line_offset:016x} '
				line = fh.read(bytes_per_line)
				chars = ''
				for byte in line:
					string += f'{byte:02x} '
					if 31 < byte < 127:
						chars += chr(byte)
					else:
						chars += '.'
				string += f'{chars}\n'
		return string

class Check:
	'''Run check'''

	def __init__(self, config):
		'''Build object'''
		sysexit(0)

class Transfer:
	'Functionality to process the whole file transfer'

	def __init__(self, config):
		'File transfer'
		decoder = PGPDecoder(config.pgp_cmd, config.pgp_passphrase)
		logging.debug(f'File / transfer infos will be stored in {config.csvpath}')
		source = Source(config)
		logging.debug(f'Source is {source.path}')
		backup = Backup(config)
		logging.debug(f'Backup is {backup.path}')
		for path, pattern in config.targets.items():
			logging.debug(f'Target is {path} for regex pattern "{pattern}"')
		logging.debug(f'Basic target is {config.targetpath}')
		newonsource = source.listfiles() - backup.fetched	# filter for new files
		if newonsource == set():
			logging.info(f'Did not find new file(s) on {source.path}')
			return
		logging.info(
			f'Found new file(s) on {source.path}: '
			+ str(newonsource).lstrip('{').rstrip('}')
		)
		fetches = list()	# to store the fetched files
		for sourcefile in newonsource:
			sourcepath, backuppath, sum_orig, ts_fetch = source.fetch(sourcefile, backup.path)
			logging.info(f'Copied {sourcepath} to {backuppath}')
			fetches.append((Path(sourcefile).name, sum_orig, ts_fetch))
		decoded = list()	# to store the decoded files
		for filename_orig, sum_orig, ts_fetch in fetches:
			backuppath = backup.path / filename_orig
			targetdir = None	# select target directory
			for path, pattern in config.targets.items():
				if match(pattern, filename_orig) != None:
					targetdir = path
					break
			if targetdir == None:
				targetdir = config.targetpath
			try:
				decodedpath = decoder.decode(backuppath, targetdir)
				logging.info(f'Decoded {backuppath} to {decodedpath}')
			except RuntimeError:
				backup.remove(backuppath)
				continue
			targetsum = backup.sha256(decodedpath)
			decoded.append({
				'filename_orig': filename_orig,
				'sum_orig': sum_orig,
				'ts_fetch': ts_fetch,
				'filename_dec': decodedpath.name,
				'sum_dec': targetsum
			})
		if decoded != list():
			backup.update_csv(decoded)

class MainLoop:
	'Main loop'

	def __init__(self, config):
		'Initiate main loop'
		self.config = config
		logging.info('Starting main loop')
		while True:	# check if trigger file exists or time matches
			if config.triggerfile.exists():
				remove(config.triggerfile)
				self.worker()
			elif datetime.now().strftime('%H:%M') in config.updates:
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
	argparser.add_argument('-f', '--logfile', type=Path, default=__path__.with_suffix('.log.txt'),
		help='Log file', metavar='FILE')
	argparser.add_argument('-l', '--loglevel', choices=('debug', 'info', 'warning', 'error', 'critical'),
		help='Log level, ignorde on -d/--debug', metavar='STRING')
	args = argparser.parse_args()
	config = Config(args.config)
	if args.debug:
		loglevel = 'debug'
	else:
		loglevel = args.loglevel
	log = Logger(args.logfile, loglevel)
	if loglevel == 'debug':
		logging.info('Starting check on debug level')
		Check(config)
		sysexit(0)
	else:
		MainLoop(config)