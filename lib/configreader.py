#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from configparser import ConfigParser
from pathlib import Path

class ConfigReader:
	'Handle the config file'

	def __init__(self, configfile):
		'Get configuration from file and initiate logging'
		config = ConfigParser()
		config.read(configfile)
		for section in config.sections():
			for name in config[section]:
				if section in ('PATHS', 'DIRS', 'FILES'):
					setattr(self, f'{name}_{section.lower().rstrip('s')}', Path(config[section][name]))
				else:
					try:
						setattr(self, f'{section.lower().rstrip('s')}_{name}', int(config[section][name]))
					except ValueError:
						setattr(self, f'{section.lower().rstrip('s')}_{name}', config[section][name])
