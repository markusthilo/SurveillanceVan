#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-07-30'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'Distribution THI'
__destination__ = 'C:/Users/THI/Documents/test_dst'
#__destination__ = '/home/neo/test/test_dst'
__logging__ = 'C:/Users/THI/Documents/test_log'
#__logging__ = '/home/neo/test/test_log'

### standard libs ###
from sys import executable as __executable__
from sys import argv as sys_argv
from sys import exit as sys_exit
from pathlib import Path
from threading import Thread
### tk libs ###
from tkinter import Tk, PhotoImage
from tkinter.font import nametofont
from tkinter.ttk import Frame, Label, Button
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askyesno, showerror
from tkinter.filedialog import askdirectory
from idlelib.tooltip import Hovertip
### custom libs ###
from lib.pathutils import PathUtils
from lib.logger import Logger
from lib.stringutils import StringUtils

class Copy:
	'''Copy functionality'''

	### hard coded configuration ###
	DST_PATH = Path(__destination__)	# root directory to copy
	LOG_PATH = Path(__logging__)	# directory to write logs that trigger surveillance
	LOG_NAME = 'log.txt' # log file name
	TSV_NAME = 'done.txt'	# csv file name - file is generaten when all is done
	MAX_PATH_LEN = 230	# throw error when paths have more chars
	ZIP_DEPTH = 2	# path depth where subdirs will be zipped
	ZIP_FILE_QUANTITY = 10	# minamal quantity of files in subdir to zip

	def __init__(self, root_dirs, echo=print):
		'''Generate object to copy and to zip'''
		self.exceptions = True
		for root_dir in root_dirs:
			root_path = Path(root_dir)
			if not root_path.is_dir():
				echo(f'Skipping {root_path}, it is not a directory')
				continue
			dirs, files = PathUtils.tree(root_path)	# get source file/dir structure
			for path in dirs | files:
				if len(f'{path.absolute()}') > self.MAX_PATH_LEN:
					echo(f'ERROR: path {path.absolute()} has more than {self.MAX_PATH_LEN} characters')
					return
			dirs2zip = {	# look for dirs with to much files for normal copy
				path: infos for path, infos in dirs.items()
				if infos['depth'] == self.ZIP_DEPTH and infos['files'] >= self.ZIP_FILE_QUANTITY
			}
			paths_to_zip = set(dirs2zip)
			dirs2copy = {	# dirs that will not be zipped
				path: infos for path, infos in dirs.items()
				if paths_to_zip - set(path.parents) == paths_to_zip
			}
			files2copy = {	# files that will not be zipped
				path: infos for path, infos in files.items()
				if paths_to_zip - set(path.parents) == paths_to_zip
			}
			dst_path = self.DST_PATH / root_path.name
			try:
				dst_path.mkdir(exist_ok=True)
			except Exception as ex:
				echo(f'Unable to generate directory {path}:\n{ex}')
				return
			log_path = self.LOG_PATH / root_path.name
			try:
				log_path.mkdir(exist_ok=True)
			except Exception as ex:
				echo(f'Unable to generate directory {path}:\n{ex}')
				return
			log_file_path = log_path / self.LOG_NAME
			log = Logger(log_file_path, info=f'Copying {root_path} to {dst_path}', echo=echo)
			tsv = 'Path\tSize\tHash'	# will later be written as tsv files
			echo(f'Generating {len(dirs2copy)} directories')
			for src_dir, infos in dirs2copy.items():
				path = dst_path / src_dir
				try:
					path.mkdir(parents=True, exist_ok=True)
				except Exception as ex:
					log.warning(f'Unable to generate directory {path}:\n{ex}')
			for src_file, infos in files2copy.items():
				echo(f'Copying {src_file}) {StringUtils.bytes(infos['size'])}')
				path = dst_path / src_file
				try:
					hash = PathUtils.copy_file(root_path  / src_file, path)
				except Exception as ex:
					log.error(f'Unable to copy source file to {path}:\n{ex}')
				else:
					if hash:
						tsv += f'\n{src_file}\t{infos["size"]}\t{hash}'
					else:
						log.error(f'Source file and {path} are not identical')
			for src_dir, infos in dirs2zip.items():
				echo(f'Zipping {src_dir}) {StringUtils.bytes(infos['size'])}')
				path = dst_path / src_dir.with_suffix('.zip')
				try:
					hash, file_errors, dir_errors = PathUtils.zip_dir(root_path  / src_dir, path)
				except Exception as ex:
					log.error(f'Unable build archive {path}:\n{ex}')
				else:
					tsv += f'\n{src_dir.with_suffix(".zip")}\t{path.stat().st_size}\t{hash}'
					if file_errors:
						log.warning(f'The following file(s) could not be zipped:\n{"\n".join(file_errors)}')
					if dir_errors:
						log.warning(f'The following dir(s) could not be build in zip:\n{"\n".join(dir_errors)}')
			dst_tsv = dst_path / self.TSV_NAME
			try:
				dst_tsv.write_text(tsv, encoding='utf-8')
			except Exception as ex:
				log.error(f'Unable to write {dst_tsv}:\n{ex}')
			log_tsv = log_path / self.TSV_NAME
			try:
				log_tsv.write_text(tsv, encoding='utf-8')
			except Exception as ex:
				log.error(f'Unable to write {log_tsv}:\n{ex}')
			if log.close():
				echo(f'{log.errors} error(s) and {log.warnings} occured while processing {root_path}')
			else:
				self.exceptions = False

class Worker(Thread):
	'''Thread that does the work while Tk is running the GUI'''

	def __init__(self, gui):
		'''Get all attributes from GUI and run Copy'''
		super().__init__()
		self.gui = gui

	def run(self):
		'''Run thread'''
		copy = Copy(self.gui.source_paths, echo=self.gui.echo)
		if copy.exceptions:
			showerror(title='Warning', message='Problems occured!')
		self.gui.finished()

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	X_FACTOR = 40
	Y_FACTOR = 30
	LABEL = __description__

	def __init__(self, icon_base64):
		'''Open application window'''
		super().__init__()
		self.worker = None
		self.title(f'SlowCopy v{__version__}')
		self.rowconfigure(1, weight=1)
		self.columnconfigure(1, weight=1)
		self.rowconfigure(3, weight=1)
		self.wm_iconphoto(True, PhotoImage(data=icon_base64))
		self.protocol('WM_DELETE_WINDOW', self._quit_app)
		font = nametofont('TkTextFont').actual()
		self.font_family = font['family']
		self.font_size = font['size']
		self.min_size_x = self.font_size * self.X_FACTOR
		self.min_size_y = self.font_size * self.Y_FACTOR
		self.minsize(self.min_size_x , self.min_size_y)
		self.geometry(f'{self.min_size_x}x{self.min_size_y}')
		self.resizable(True, True)
		self.padding = int(self.font_size / self.PAD)
		frame = Frame(self)
		frame.grid(row=0, column=0, columnspan=2, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		Label(frame, text=self.LABEL).pack(padx=self.padding, pady=self.padding)
		frame = Frame(self)
		frame.grid(row=1, column=0,	sticky='n')
		self.source_button = Button(frame, text='Source', command=self._add_dir)
		self.source_button.pack(padx=self.padding, pady=self.padding, fill='x', expand=True)
		Hovertip(self.source_button, 'Add directory you want to copy')
		self.source_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.source_text.grid(row=1, column=1, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		frame = Frame(self)
		frame.grid(row=2, column=1, sticky='news', padx=self.padding, pady=self.padding)
		Label(frame, text='Copy to import directory').pack(padx=self.padding, pady=self.padding, side='left')
		self.exec_button = Button(frame, text='Execute', command=self._execute)
		self.exec_button.pack(padx=self.padding, pady=self.padding, side='right')
		Hovertip(self.exec_button, 'Start copy process')
		self.info_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.info_text.grid(row=3, column=0, columnspan=2, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		self.info_text.bind('<Key>', lambda dummy: 'break')
		self.info_text.configure(state='disabled')

	def _add_dir(self):
		directory = askdirectory(title='Select directory to copy', mustexist=True)
		if directory:
			self.source_text.insert('end', f'{directory}\n')

	def echo(self, *arg):
		'''Write message to info field (ScrolledText)'''
		msg = ' '.join(arg)
		self.info_text.configure(state='normal')
		self.info_text.insert('end', f'{msg}\n')
		self.info_text.configure(state='disabled')
		self.info_text.yview('end')

	def _execute(self):
		source_paths = self.source_text.get('1.0', 'end').strip()
		if not source_paths:
			return
		self.source_button.configure(state='disabled')
		self.source_text.configure(state='disabled')
		self.exec_button.configure(state='disabled')
		self.info_text.configure(state='normal')
		self.info_text.delete('1.0', 'end')
		self.info_text.configure(state='disabled')
		self.source_paths = source_paths.split('\n')
		self.worker = Worker(self)
		self.worker.start()

	def finished(self):
		'''Run this when Worker has finished'''
		self.source_text.configure(state='normal')
		self.source_text.delete('1.0', 'end')
		self.source_button.configure(state='normal')
		self.exec_button.configure(state='normal')
		self.worker = None

	def _quit_app(self):
		if self.worker and not askyesno(
			title='Copy process is running!',
			message='Are you sure to kill copy process / application?'
		):
			return
		self.destroy()

if __name__ == '__main__':  # start here
	if len(sys_argv) > 1:
		copy = Copy(sys_argv[1:])
		if copy.exceptions:		
			sys_exit(1)
		sys_exit(0)
	else:
		Gui('''iVBORw0KGgoAAAANSUhEUgAAADAAAAAwCAMAAABg3Am1AAACEFBMVEUAAAH7AfwVFf8WFv4XF/0Y
GPwZGfwaGvsaGvwbG/scHPodHfkeHvkfH/kgIPggIPkhIfciIvYjI/UkJPUlJfQnJ/IoKPEpKfAq
KvArK+4rK+8sLO4tLewtLe0uLusuLuwvL+swMOoxMegxMekyMuczM+UzM+Y0NOQ0NOU1NeM1NeQ1
NeU2NuE2NuI2NuM3N+A3N+E4ON85Od45Od86Otw6Ot07O9o7O9s8PNk8PNs9Pdg9Pdk+PtY+Ptc/
P9RAQNJAQNNAQNRBQdBBQdFBQdJCQs5CQs9CQtBDQ81DQ85ERMpERMtERMxFRclFRcpGRsZGRsdH
R8RHR8VHR8ZISMJISMNJScBJScFKSr1KSr5KSr9LS7tMTLhMTLlMTLpNTbdNTbhOTrROTrVPT7FP
T7JPT7NQUK1QUK5QUK9QULBRUapRUatRUaxSUqZSUqdSUqhSUqlSUqpTU6RTU6ZUVKFUVKJUVKNV
VZ1VVZ5VVZ9VVaFWVplWVppWVptWVpxXV5VXV5ZXV5dXV5hYWJFYWJJYWJNYWJRZWY5ZWY9ZWZBa
WohaWolaWopaWotbW4RbW4ZbW4dcXH5cXH9cXIBcXIFcXIJcXINdXXldXXpdXXtdXXxdXX1eXnNe
XnVeXnZeXndeXnhfX21fX25fX3BfX3FfX3JgYGVgYGZgYGdgYGlgYGpgYGtgYGxhYWFhYWJhYWRt
OtjpAAAAAXRSTlMAQObYZgAAAWlJREFUSMftlc9LAkEUx4e3KrqXWAg6hUEh4T0shQgKRArpEEUb
4pKS0TEMAulWrEF4yKOC5WFbD9/xX2xWwx/pLDtEdfF72n3f72fezJuFZWyhfxV+G1DMA4rYEIBC
HpI8hgqax1gzdTa7zmR+2p3f91t+wod0oxIiaH40+7kA0KuXKnZ3YLmNm1Ktzb8yEsBeJ6GVK+HU
k2HxaOQ5plpP59/jFEls6NoD8GyQtpY06BR+wCOR2e+/ljmcTYpUXP5mNQah+VcDVImKw3otRLsT
IRnQ1Ek/63j1E9LuxiHIAJ7XiJYLPWCfojbkQx6N2jlfEqNJudij2EsQAGjldO8ghxR+CgYA9zHa
RpHICgDYTXGxXYMyaMVotS18/uELXES3TCulURn8iChuWseJa1+g4H0YFEq7os9OaPBS8gEY2pVs
OpO9dT3HqebSmYPLji8QQEyVYIoEY4qE6o5+cgD8xYF9mcXPV12fPIIrXx13KAAAAAAASUVORK5C
YII=''').mainloop()

