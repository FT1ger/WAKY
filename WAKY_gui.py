import os
import re
import tkinter as tk
from tkinter.filedialog import askopenfilename
from tkinter.messagebox import showinfo
from tkinter.scrolledtext import ScrolledText
from WAKY_token import *
from platform import system


"""
Nuitka packaging

MacOS (with pyenv support):
export TCL_LIBRARY=/opt/homebrew/lib/tcl9.0
export TK_LIBRARY=/opt/homebrew/lib/tk9.0 
nuitka --standalone --macos-create-app-bundle --macos-app-icon=icon.icns --include-data-files=icon.gif=icon.gif --static-libpython=no --enable-plugin=tk-inter --output-filename=WAKY-1.0.0-MacOS WAKY_gui.py

Windows:
nuitka --standalone --onefile --windows-icon-from-ico=icon.ico --include-data-files=icon.ico=icon.ico --enable-plugin=tk-inter --output-filename=WAKY-1.0.0-Windows WAKY_gui.py

"""




class MainApplication(tk.Frame):
    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        self.parent = parent

        # Place a label "File 1:" and right edge sticks to EAST (right edge)
        tk.Label(self, text='R file:').grid(row=0, column=0, padx=5, pady=5, sticky=tk.E)
        # Place a button "Select File" and right edge sticks to EAST (right edge)
        self.file_name_r = tk.StringVar()
        tk.Entry(self, width=60, textvariable=self.file_name_r, state='readonly').grid(row=0, column=1, padx=5, pady=5)
        # Place a button "Select File" and right edge sticks to EAST (right edge)
        self.btn_file_r = tk.Button(self, text='Browse...', command=lambda: self.select_file(self.file_name_r, 'r'))
        self.btn_file_r.grid(row=0, column=2, padx=5, pady=5)

        # Place a label "File 2:" and right edge sticks tos EAST (right edge)
        tk.Label(self, text='Rmd file:').grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)
        # Place a button "Select File" and right edge sticks to EAST (right edge)
        self.file_name_rmd = tk.StringVar()
        tk.Entry(self, width=60, textvariable=self.file_name_rmd, state='readonly').grid(row=1, column=1, padx=5, pady=5)
        # Place a button "Select File" and right edge sticks to EAST (right edge)
        self.btn_file_rmd = tk.Button(self, text='Browse...', command=lambda: self.select_file(self.file_name_rmd, 'rmd'))
        self.btn_file_rmd.grid(row=1, column=2, padx=5, pady=5)

        # Place a button "Run process" and left/right edges stick to EAST and WEST
        self.btn_run = tk.Button(self, text='Run', command=self.process_file).grid(
            row=2, column=1, padx=5, pady=5, sticky=tk.EW)

        # Place a scrollable text frame to show result
        self.result = ScrolledText(self, height=10)
        self.result.config(state='disabled')
        self.result.grid(row=3, column=0, columnspan=3, padx=5, pady=5)

    def select_file(self, var: tk.StringVar, r_or_rmd:str):
        if r_or_rmd == 'r':
            file_name = askopenfilename(
                # initialdir=os.path.dirname(__file__),   # Current directory of this script
                filetypes=(
                    ('R script', '*.R'),
                ))
        else:
            file_name = askopenfilename(
                # initialdir=os.path.dirname(__file__),   # Current directory of this script
                filetypes=(
                    ('Rmd file', '*.Rmd'),
                ))
        
        var.set(file_name)

    def process_file(self):
        try:
            result_str = file_process_func(self.file_name_r.get(), self.file_name_rmd.get())
        except Exception as e:
            result_str = 'Error happend!\n'
            result_str += f'  {e.__class__.__name__}: {e.args[0]}'
        self.result.config(state='normal')
        self.result.delete("1.0", tk.END)
        self.result.insert(tk.END, result_str)
        self.result.config(state='disabled')

def file_process_func(r_file, rmd_file):
    result_str = ''
    if not r_file:
        raise RuntimeError('R file not found')
    if m:=re.match(r'a(\d)_(\d+)_1.R', os.path.basename(r_file)):
        ysn = int(m[2])
    if r_file:
        checkers = [
            DS2_Checker_ysn_seed,
            DS3_Checker_invalid_char,
            DS3_Checker_contains_comments,
            ReminderSheetChecker('better_reminder.csv'),
        ]
        if rmd_file:
            checkers.append(DS5_Checker_same_contains_r(rmd_file))
        cc = CheckerContext(r_file, ysn, checkers=checkers)
        print(cc.error_marked_content)
        with open(f'checker_{cc.ysn}.r.log', 'w', encoding=cc.encoding) as fo:
            for err in cc.errors:
                if isinstance(err, (WAKYReminderSheetCheckInfo,)):
                    # skip highlight info from logging
                    continue
                print(err, file=fo)
    if rmd_file:
        cc = CheckerContext(rmd_file, ysn, checkers=[
            DS2_Checker_ysn_seed,
            DS3_Checker_invalid_char,
            DS3_Checker_contains_comments_rmd,
        ])
        # print(cc.error_marked_content)
        with open(f'checker_{cc.ysn}.rmd.log', 'w', encoding=cc.encoding) as fo:
            for err in cc.errors:
                if isinstance(err, (WAKYReminderSheetCheckInfo,)):
                    # skip highlight info from logging
                    continue
    if os.path.exists(f'checker_{cc.ysn}.r.log'):
        with open(f'checker_{cc.ysn}.r.log', 'r', encoding=cc.encoding) as fo:
            result_str += 'R file log: \n'
            result_str += fo.read()
    if os.path.exists(f'checker_{cc.ysn}.rmd.log'):
        with open(f'checker_{cc.ysn}.rmd.log', 'r', encoding=cc.encoding) as fo:
            result_str += 'Rmd file log: \n'
            result_str += fo.read()
    return result_str


if __name__ == "__main__":
    root = tk.Tk()
    MainApplication(root).pack(side="top", fill="both", expand=True)
    root.title("WAKY")
    if system() == 'Darwin':
        img = tk.Image("photo", file="icon.gif")
        root.iconphoto(True, img)
        root.tk.call('wm','iconphoto', root._w, img)
    elif system() == 'Windows':
        root.iconbitmap('icon.ico')
    root.resizable(False, False)
    root.mainloop()