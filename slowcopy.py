#!/usr/bin/env python3
# -*- coding: utf-8 -*-

__app_name__ = 'SlowCopy'
__author__ = 'Markus Thilo'
__version__ = '0.0.1_2024-07-18'
__license__ = 'GPL-3'
__email__ = 'markus.thilo@gmail.com'
__status__ = 'Testing'
__description__ = '''
Copy directories and generate hashes
'''

from sys import executable as __executable__
from pathlib import Path
from functools import partial
from tkinter import Tk, PhotoImage
from tkinter.font import nametofont
from tkinter.ttk import Frame, LabelFrame, Label, Button, Separator
from tkinter.scrolledtext import ScrolledText
from tkinter.messagebox import askyesno, showerror, showwarning
from tkinter.filedialog import askdirectory, askopenfilename
from idlelib.tooltip import Hovertip

if Path(__executable__).stem == __app_name__.lower():
	__parent_path__ = Path(__executable__).parent
else:
	__parent_path__ = Path(__file__).parent

class Van:
	'''Simple communication to server using socket'''

	def __init__(self):
		'''Establish connection'''
		pass

class Gui(Tk):
	'''GUI look and feel'''

	PAD = 4
	X_FACTOR = 40
	Y_FACTOR = 30

	def __init__(self, icon_base64):
		'Open application window'
		super().__init__()
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
		button = Button(frame, text='Source', command=self._add_dir)
		button.pack(padx=self.padding, pady=self.padding, fill='x', expand=True)
		Hovertip(button, 'Add directory you want to copy')
		self.source_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.source_text.grid(row=0, column=1, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		frame = Frame(self)
		frame.grid(row=1, column=0, columnspan=2, sticky='news', padx=self.padding, pady=self.padding)
		button = Button(frame, text='Execute', command=self._execute)
		button.pack(padx=self.padding, pady=self.padding, side='right')
		Hovertip(button, 'Start copy process')
		self.info_text = ScrolledText(self, font=(self.font_family, self.font_size),
			padx = self.padding, pady = self.padding)
		self.info_text.grid(row=2, column=0, columnspan=2, sticky='news',
			ipadx=self.padding, ipady=self.padding, padx=self.padding, pady=self.padding)
		self.info_text.bind('<Key>', lambda dummy: 'break')
		self.info_text.configure(state='disabled')

	def ask_warning(self, msg):
		return askyesno(f'{__app_name__}: Warning', msg, icon='warning')

	def echo(self, msg):
		self.info_text.configure(state='normal')
		self.info_text.insert('end', '{msg}\n')
		self.info_text.configure(state='disabled')
		self.info_text.yview('end')

	def clear(self, msg):
		self.info_text.configure(state='normal')
		self.info_text.delete('1.0', 'end')
		self.info_text.configure(state='disabled')

	def _add_dir(self):
		directory = askdirectory(title='Select directory to copy', mustexist=True)
		if directory:
			self.source_text.insert('end', f'{directory}\n')

	def _execute(self):
		root_paths = [ Path(line.strip())
			for line in self.source_text.get('1.0', 'end').split('\n') if line.strip()
		]
		self.source_text.delete('1.0', 'end')
		print(root_paths)

	def _quit_app(self):
		self.destroy()


if __name__ == '__main__':  # start here
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
