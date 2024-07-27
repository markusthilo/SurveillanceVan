#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'SlowCopy'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-07-27'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Copy directories to a fixed destination and write logs
'''

### standard libs ###
from sys import executable as __executable__
from sys import argv as sys_argv
from sys import exit as sys_exit
from pathlib import Path
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

if Path(__executable__).stem == __app_name__.lower():
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class Copy:
	'''Copy functionality'''

	DST_PATH = Path('test_dst')	# root directory to copy
	LOG_PATH = Path('test_log')	# directory to write logs that trigger surveillance
	LOG_NAME = 'log.txt' # Log file name
	ZIP_DEPTH = 2	# path depth where subdirs will be zipped
	ZIP_FILE_QUANTITY = 10	# minamal quantity of files in subdir to zip

	def __init__(self, root_dirs, echo=print):
		'''Generate object to copy and to zip'''
		for root_dir in root_dirs:
			root_path = Path(root_dir)
			if not root_path.is_dir():
				echo(f'Skipping {root_path}, it is not a directory')
				continue
			dirs, files = PathUtils.tree(root_path)	# get source file/dir structure
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
			dst_path = self.DST_PATH / root_path.name	# generete destination directories
			dst_path.mkdir(parents=True, exist_ok=True)	# if necessary
			log_path = self.LOG_PATH / root_path.name
			log_path.mkdir(parents=True, exist_ok=True)
			log_file_path = log_path / self.LOG_NAME
			log = Logger(log_file_path, info=f'Copying {root_path} to {dst_path}', echo=echo)
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
						files2copy[src_file]['hash'] = hash
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
					dirs2zip[src_dir]['hash'] = hash
					if file_errors:
						log.warning(f'The following file(s) could not be zipped:\n{"\n".join(file_errors)}')
					if dir_errors:
						log.warning(f'The following dir(s) could not be build in zip:\n{"\n".join(dir_errors)}')
			if log.close():
				echo(f'{log.errors} error(s) and {log.warnings} occured while processing {root_path}')

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	X_FACTOR = 40
	Y_FACTOR = 30

	def __init__(self, icon_base64):
		'''Open application window'''
		super().__init__()
		self.busy = False
		self.title(f'{__app_name__} v{__version__}')
		self.rowconfigure(0, weight=1)
		self.columnconfigure(1, weight=1)
		self.rowconfigure(2, weight=1)
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
		frame.grid(row=0, column=0,	sticky='n')
		self.source_button = Button(frame, text='Source', command=self._add_dir)
		self.source_button.pack(padx=self.padding, pady=self.padding, fill='x', expand=True)
		Hovertip(self.source_button, 'Add directory you want to copy')
		self.source_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.source_text.grid(row=0, column=1, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		frame = Frame(self)
		frame.grid(row=1, column=1, sticky='news', padx=self.padding, pady=self.padding)
		Label(frame, text='Copy to import directory').pack(padx=self.padding, pady=self.padding, side='left')
		self.exec_button = Button(frame, text='Execute', command=self._execute)
		self.exec_button.pack(padx=self.padding, pady=self.padding, side='right')
		Hovertip(self.exec_button, 'Start copy process')
		self.info_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.info_text.grid(row=2, column=0, columnspan=2, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		self.info_text.bind('<Key>', lambda dummy: 'break')
		self.info_text.configure(state='disabled')

	def _add_dir(self):
		directory = askdirectory(title='Select directory to copy', mustexist=True)
		if directory:
			self.source_text.insert('end', f'{directory}\n')

	def echo(self, msg):
		'''Write message to info field (ScrolledText)'''
		self.info_text.configure(state='normal')
		self.info_text.insert('end', f'{msg}\n')
		self.info_text.configure(state='disabled')
		self.info_text.yview('end')

	def _execute(self):
		source_paths = self.source_text.get('1.0', 'end').strip()
		if not source_paths:
			return
		self.busy = True
		self.source_button.configure(state='disabled')
		self.source_text.configure(state='disabled')
		self.exec_button.configure(state='disabled')
		self.info_text.configure(state='normal')
		self.info_text.delete('1.0', 'end')
		self.info_text.configure(state='disabled')
		cp = Copy(source_paths, echo=self.echo)
		self.source_text.configure(state='normal')
		self.source_text.delete('1.0', 'end')
		self.source_button.configure(state='normal')
		self.exec_button.configure(state='normal')
		self.busy = False

	def _quit_app(self):
		if self.busy and not askyesno(
			title='Copy process is running!',
			message='Are you sure to close client application?'
		):
			return
		self.destroy()

if __name__ == '__main__':  # start here
	if len(sys_argv) > 1:
		cp = Copy(sys_argv[1:])
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
