#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.1_2024-07-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Watch copy processes'

import logging
from pathlib import Path
from filecmp import cmp as filecmp
from socket import socket, gethostname, gethostbyname, AF_INET, SOCK_STREAM
from threading import Thread
from sys import exit as sysexit
from time import sleep
from datetime import datetime
from configparser import ConfigParser
from argparse import ArgumentParser

class PathUtils:
	'''Add some methods to pathlib´s Path Class'''

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
		if path.is_dir():
			return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
		if path.is_file():
			return path.stat().st_size

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
	def quantitiy(root):
		'''Get quantitiy of all items'''
		return len(list(root.rglob('*')))

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

class Config:
	'Handle the config file'

	def __init__(self, configfile):
		'Get configuration from file and initiate logging'
		config = ConfigParser()
		config.read(configfile)
		self.server_port = config['SERVER']['port']
		self.work_path = Path(config['WORK']['path'])
		self.backup_path = Path(config['BACKUP']['path'])

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

class Check:
	'''Run check'''

	def __init__(self, config):
		'''Build object'''
		logging.info(f'Checking what is missing in {config.work_path} compared to to {config.backup_path}')
		tc = TreeCmp(config.work_path, config.backup_path)
		if len(tc.missing) == 0:
			logging.info('Nothing is missing')
		else:
			msg = f'{len(tc.missing)} missing path(s):'
			for path, tp in tc.missing:
				msg += f'\n\t{tp}:\t{path}'
			logging.info(msg)

class Server:
	'''Socket TCP server'''

	def __init__(self, port):
		'''Build object for rhe server'''
		self.hostname = gethostname()
		self.host = gethostbyname(self.hostname)
		self._server = socket(AF_INET, SOCK_STREAM)
		self._server.bind((self.host, self.port))

	def wait(self):
		'''Wait for clients'''
		self._server.listen()
		self._connection, address = self._server.accept()
		return address, self._connection.recv(4096)

	def echo(self, msg):	
		'''Send message to client'''
		self._connection.sendall(msg.encode())

	def close(self):
		'''Terminate connection to client'''
		self._connection.close()
			

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
	argparser.add_argument('-f', '--logfile', type=Path, default=__path__.with_suffix('.log.txt'),
		help='Log file', metavar='FILE')
	argparser.add_argument('-l', '--loglevel', choices=('debug', 'info', 'warning', 'error', 'critical'),
		default='debug', help='Log level, ignorde on -d/--debug', metavar='STRING')
	args = argparser.parse_args()
	config = Config(args.config)
	if args.debug:
		loglevel = 'debug'
	else:
		loglevel = args.loglevel
	log = Logger(args.logfile, loglevel)
	
	server = Server()
	print(server.wait())
	server.echo('TEST1')
	server.echo('test2')
	server.close()
	
	
	'''
	if loglevel == 'debug':
		logging.debug('Starting check on debug level')
		Check(config)
		print(Path(args.logfile.read_text()))
		sysexit(0)
	else:
		MainLoop(config)
	'''