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
				attribute_name = f'{name}_{section.lower().rstrip('s')}'
				if section == 'PATHS':
					setattr(self, attribute_name, Path(config[section][name]))
				else:
					try:
						setattr(self, attribute_name, int(config[section][name]))
					except ValueError:
						setattr(self, attribute_name, config[section][name])