#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-09-02'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = 'TEST - LKA 71'
__destination__ = 'C:\\Users\\THI\\Documents\\test_dst\\dep1'
#__destination__ = '/home/neo/Documents/test_dst'
__logging__ = 'C:\\Users\\THI\\Documents\\test_trigger\\dep1'
#__logging__ = '/home/neo/Documents/test_log\dep1'

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
	LOG_NAME = 'log.txt' # log file name
	TSV_NAME = 'done.txt'	# csv file name - file is generaten when all is done
	MAX_PATH_LEN = 230	# throw error when paths have more chars
	ZIP_DEPTH = 2	# path depth where subdirs will be zipped
	ZIP_FILE_QUANTITY = 1000	# minamal quantity of files in subdir to zip
	### paths ###
	DST_PATH = Path(__destination__)	# root directory to copy
	LOG_PATH = Path(__logging__)	# directory to write logs that trigger surveillance

	def __init__(self, root_dirs, echo=print):
		'''Generate object to copy and to zip'''
		self.exceptions = True
		for root_dir in root_dirs:	# loop through all given root dirs
			root_path = Path(root_dir.strip('"').strip("'").strip())	# make sure f**king win gets pure path
			echo(f'Preparing to copy {root_path}')
			if not root_path.is_dir():
				echo(f'ERROR: {root_path} it is not a directory')
				return
			dirs, files = PathUtils.tree(root_path)	# get source file/dir structure
			for path in dirs | files:	# check length of all paths
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
			all_files = len(files2copy) + len(dirs2zip)	# how much files to copy?
			counter = 1
			total_size = 0
			for src_file, infos in files2copy.items():	# loop to copy files
				echo(f'Copying {src_file}) ({counter} of {all_files}, {StringUtils.bytes(infos['size'])})')
				path = dst_path / src_file
				try:
					hash = PathUtils.copy_file(root_path / src_file, path)
				except Exception as ex:
					log.error(f'Unable to copy source file to {path}:\n{ex}')
				else:
					counter += 1
					total_size += infos['size']
					if hash:
						tsv += f'\n{src_file}\t{infos["size"]}\t{hash}'
					else:
						log.error(f'Source file and {path} are not identical')
			for src_dir, infos in dirs2zip.items():	# loop to zip files
				echo(f'Zipping {src_dir} ({counter} of {all_files}, {StringUtils.bytes(infos['size'])})')
				path = dst_path / src_dir.with_suffix('.zip')
				try:
					hash, file_errors, dir_errors = PathUtils.zip_dir(root_path  / src_dir, path)
				except Exception as ex:
					log.error(f'Unable build archive {path}:\n{ex}')
				else:
					counter += 1
					size = path.stat().st_size
					total_size += size
					tsv += f'\n{src_dir.with_suffix(".zip")}\t{size}\t{hash}'
					log.info(f'Zipped {src_dir}', echo=False)
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
			log.info(f'Wrote {counter-1} files / {total_size} Bytes ({StringUtils.bytes(total_size)}) to {dst_path}')
			if log.close():
				echo(f'{log.errors} error(s) and {log.warnings} occured while processing {root_path}')
			else:
				echo('Finished successfully')
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
		self.gui.finished(copy.exceptions)

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	X_FACTOR = 40
	Y_FACTOR = 30
	LABEL = __description__
	GREEN_FG = 'black'
	GREEN_BG = 'pale green'
	RED_FG = 'black'
	RED_BG = 'coral'

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
		frame = Frame(self)
		frame.grid(row=3, column=0,	sticky='n')
		self.clear_button = Button(frame, text='Clear', command=self._clear_info)
		self.clear_button.pack(padx=self.padding, pady=self.padding, fill='x', expand=True)
		Hovertip(self.clear_button, 'Clear info field')
		self.info_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.info_text.grid(row=3, column=1, columnspan=1, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		self.info_text.bind('<Key>', lambda dummy: 'break')
		self.info_text.configure(state='disabled')
		self.info_fg = self.info_text.cget('foreground')
		self.info_bg = self.info_text.cget('background')
		frame = Frame(self)
		frame.grid(row=4, column=1, sticky='news', padx=self.padding, pady=self.padding)
		self.info_label = Label(frame)
		self.info_label.pack(padx=self.padding, pady=self.padding, side='left')
		self.label_fg = self.info_label.cget('foreground')
		self.label_bg = self.info_label.cget('background')
		self.quit_button = Button(frame, text='Quit', command=self._quit_app)
		self.quit_button.pack(padx=self.padding, pady=self.padding, side='right')
		self._init_warning()

	def _add_dir(self):
		'''Add directory into field'''
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

	def _clear_info(self):
		'''Clear info text'''
		self.info_text.configure(state='normal')
		self.info_text.delete('1.0', 'end')
		self.info_text.configure(state='disabled')
		self.info_text.configure(foreground=self.info_fg, background=self.info_bg)
		self._warning_state = 'stop'

	def _execute(self):
		'''Start copy process / worker'''
		source_paths = self.source_text.get('1.0', 'end').strip()
		if not source_paths:
			return
		self.source_button.configure(state='disabled')
		self.source_text.configure(state='disabled')
		self.exec_button.configure(state='disabled')
		self._clear_info()
		self.quit_button.configure(state='disabled')
		self.source_paths = source_paths.split('\n')
		self.worker = Worker(self)
		self.worker.start()

	def _init_warning(self):
		'''Init warning functionality'''
		self._warning_state = 'disabled'
		self._warning()

	def _warning(self):
		'''Show flashing warning'''
		if self._warning_state == 'enable':
			self.info_label.configure(text='WARNING')
			self._warning_state = '1'
		if self._warning_state == '1':
			self.info_label.configure(foreground=self.RED_FG, background=self.RED_BG)
			self._warning_state = '2'
		elif self._warning_state == '2':
			self.info_label.configure(foreground=self.label_fg, background=self.label_bg)
			self._warning_state = '1'
		elif self._warning_state != 'disabled':
			self.info_label.configure(text= '', foreground=self.label_fg, background=self.label_bg)
			self._warning_state = 'disabled'
		self.after(500, self._warning)

	def finished(self, exceptions):
		'''Run this when Worker has finished'''
		self.source_text.configure(state='normal')
		self.source_text.delete('1.0', 'end')
		self.source_button.configure(state='normal')
		self.exec_button.configure(state='normal')
		self.quit_button.configure(state='normal')
		self.worker = None
		if exceptions:
			self.info_text.configure(foreground=self.RED_FG, background=self.RED_BG)
			self._warning_state = 'enable'
			showerror(title='Warning', message='Problems occured!')
		else:
			self.info_text.configure(foreground=self.GREEN_FG, background=self.GREEN_BG)

	def _quit_app(self):
		'''Quit app, ask when copy processs is running'''
		if self.worker and not askyesno(
			title='Copy process is running!',
			message='Are you sure to kill copy process / application?'
		):
			return
		self.destroy()

if __name__ == '__main__':  # start here when run as application
	if len(sys_argv) > 1:	# when arguments / dirs are given, run on command line
		copy = Copy(sys_argv[1:])
		if copy.exceptions:	# exit code 0 when there are any exceptions
			sys_exit(1)
		sys_exit(0)
	else:	# open gui if no argument is given
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
YII=''').mainloop()	# give tk the icon as base64 and open main window
