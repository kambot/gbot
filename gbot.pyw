import pandas as pd
import numpy as np
import os

from shutil import which
from getpass import getuser
from time import strftime, sleep, time, mktime
from datetime import datetime
from subprocess import Popen

import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QFont, QSyntaxHighlighter, QTextCharFormat, QKeyEvent, QTextCursor
from PyQt5.QtCore import Qt, pyqtSignal, QObject, QEvent, QTimer, QThread, QCoreApplication


class GBot(QMainWindow):

    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):

        self.pid = os.getpid()

        self.tray_app = False

        self.root = os.path.dirname(os.path.abspath(__file__))  + "\\"
        self.support = self.root + "support\\"


        self.pypath = which("python.exe")
        if self.pypath == None:
            self.pypath = r"python.exe"

        self.pywpath = which("pythonw.exe")
        if self.pywpath == None:
            self.pywpath = r"pythonw.exe"

        self.gbts_dict = {}
        self.gbts_dict2 = {}

        self.user = getuser()

        self.appd = "C:\\Users\\"+ self.user +"\\AppData\\Local\\GBot\\"
        if not(os.path.isdir(self.appd)):
            os.makedirs(self.appd)

        self.appd_t = self.appd + "TASKS"
        self.paths = self.appd + "PATHS"
        self.select_path = self.appd + "SELECTIONS"
        self.font_path = self.appd + "FONT"

        self.path_mgmt(update=False)

        # used for the input editor
        self.inp = '''# example task\n# yyyy.mm.dd.HH.MM:00; example.cmd; 0; 0\n'''
        if os.path.isfile(self.appd_t):
            with open(self.appd_t,'r') as f:
                lines = f.read()
            self.inp = lines

        self.readme_path = self.root + "README.txt"

        self.pt = ""
        self.log = ""
        self.do_log = True
        self.prev_lines = "" # for the task window
        self.prev_msgs = "" # for the countdown window
        self.dates = {} # store the task dates
        self.save_file = 0
        self.scheds = []
        self.font_choice = ""
        self.fonts = ['Consolas','Arial']

        self.sid = 60*60*24


        # GUI Stuff -----------------------------------------------------------------------------------

        self.main_icon = QIcon(self.support + r"green_robot.png")

        self.update_font(update = False)

        self.in_tray = False
        self.was_tray = False
        self.task_count = 0

        self.statusbar = self.statusBar()
        self.statusbar.showMessage('Ready')

        self.setWindowTitle('GBot') 
        self.setWindowIcon(self.main_icon)
        

        self.chkBoxLayout = QVBoxLayout()
        self.chkBoxLayout.setAlignment(Qt.AlignTop)
        # checkbox container widget       
        self.cwidget = QWidget()  
        self.cwidget.setLayout(self.chkBoxLayout)
        # checkbox scroll area, gives scrollable view on widget
        self.scroll = QScrollArea()
        self.scroll.setMinimumWidth(100)
        self.scroll.setMaximumWidth(200)
        self.scroll.setWidgetResizable(True)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)         
        self.scroll.setWidget(self.cwidget)
        self.scroll.setToolTip('This window displays all of the .gbt files that exist in the gbt folder.')

        self.widget = QWidget()
        
        self.lbl1 = QLabel('\nSelect .gbt files', self)
        self.lbl2 = QLabel('\nCountdown', self)
        self.lbl3 = QLabel('\nTasks', self)
        self.lbl4 = QLabel('Log', self)
        self.lbl5 = QLabel('Task Editor', self)

        def make_disabled(_obj):
            _obj.setReadOnly(True)

        self.text_countdown = QTextEdit()
        make_disabled(self.text_countdown)
        self.highlighter2 = Highlighter2(self.text_countdown.document())
        self.text_countdown.setToolTip('This window displays countdowns of the scheduled tasks.')

        self.text_tasks = QTextEdit()
        make_disabled(self.text_tasks)
        self.text_tasks.setToolTip('This window displays all of the scheduled tasks.')

        self.text_log = QTextEdit()
        make_disabled(self.text_log)
        self.highlighter = Highlighter(self.text_log.document())
        self.text_log.setToolTip('This window displays logs of when tasks were initiated.')

        self.text_editor = FileEdit()
        self.text_editor.setPlainText(self.inp)
        self.text_editor.setToolTip('Use this window to create tasks outside of a gbt file.')
        self.text_editor.installEventFilter(self)       
        

        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        self.grid.addWidget(self.lbl1, 0, 0)
        self.grid.addWidget(self.scroll, 1, 0, 3, 1)
        self.grid.addWidget(self.lbl2, 0, 1)
        self.grid.addWidget(self.text_countdown, 1, 1)
        self.grid.addWidget(self.lbl3, 0, 2)
        self.grid.addWidget(self.text_tasks, 1, 2)
        self.grid.addWidget(self.lbl4, 2, 1)
        self.grid.addWidget(self.text_log, 3, 1)
        self.grid.addWidget(self.lbl5, 2, 2)
        self.grid.addWidget(self.text_editor, 3, 2)

        self.widget.setLayout(self.grid)
    
        self.setCentralWidget(self.widget)

        self.update_gbts()
        self.select_history(update=False)

        self.timer = QTimer()
        self.timer.timeout.connect(self.updater)
        self.timer.start(100)

        self.setGeometry(300, 300, 1000, 600)
        self.center()

    def update_countdown(self):
        self.lbl1.setText("Time: " + strftime("%Y.%m.%d.%H.%M:%S") + "\nSelect .gbt files")

    def update_task_label(self):
        self.lbl3.setText("\nTasks (" + str(self.task_count) + ")")

    def get_memory_usage(self):
        out = os.popen("tasklist | findstr " + str(self.pid)).read()
        out = " ".join(out.split())
        mem = " ".join(out.split(" ")[-2:])
        return mem

    def update_font(self, update):

        if not os.path.isfile(self.font_path):
            if self.font_choice == "":
                font_choice = self.fonts[0]
            with open(self.font_path,'w') as f:
                f.write(font_choice)
        
        if not update:
            with open(self.font_path,'r') as f:
                lines = f.readlines()
            
            lines = [x.strip().lower() for x in lines if x.strip() != ""]
            matches = [x for x in lines if x in [y.lower() for y in self.fonts]]
            if len(matches) > 0:
                match = matches[0]
                self.font_choice = self.fonts[[y.lower() for y in self.fonts].index(match)]
            else:
                self.font_choice = self.fonts[0]

        else:
            with open(self.font_path,'w') as f:
                f.write(self.font_choice)

        self.setFont(QFont(self.font_choice, 10))
        QToolTip.setFont(QFont(self.font_choice, 10))

    def updater(self):
        t0 = time()
        self.update_gbts()
        self.read_tasks()
        self.update_countdown()
        self.tray_tool_tip()
        self.update_task_label()
        
        self.save_file += 1
        if self.save_file == 100:
            with open(self.appd_t,'w') as f:
                f.write(self.text_editor.toPlainText())
            self.save_file = 0
        
        self.ct = strftime("%Y.%m.%d.%H.%M:%S")
        sct = str(self.ct)
        self.cts = mktime(datetime.strptime(self.ct,"%Y.%m.%d.%H.%M:%S").timetuple())

        from numpy import arange, array

        ct_lst = self.ct.split('.')
        cy = ct_lst[0]
        cm = ct_lst[1]
        cd = ct_lst[2]
        cH = ct_lst[3]
        cM = ct_lst[4].split(':')[0]
        cS = ct_lst[4].split(':')[1]

        years = [cy,str(int(cy)+1)]
        months = [str(x).zfill(2) for x in range(1,12+1)]
        days = [str(x).zfill(2) for x in range(1,31+1)]
        hours = [str(x).zfill(2) for x in range(0,23+1)]
        mins = [str(x).zfill(2) for x in range(0,59+1)]
        secs = [cS,'00']

        # need to check the current, next, and first
        d = [x % len(days) for x in days.index(cd) + arange(0,2)]
        d = list(set(array(days)[d].tolist() + [days[0]]))
        m = [x % len(months) for x in months.index(cm) + arange(0,2)]
        m = list(set(array(months)[m].tolist() + [months[0]]))
        H = [x % len(hours) for x in hours.index(cH) + arange(0,2)]
        H = list(set(array(hours)[H].tolist() + [hours[0]]))
        M = [x % len(mins) for x in mins.index(cM) + arange(0,2)]
        M = list(set(array(mins)[M].tolist() + [mins[0]]))


        msgs = []
        window_msgs = []
        tray_msgs = []
        added_log = False
        files_exist = {}
        self.log = ""

        if self.recalc:
            self.dates = {}

        # [loop through the scheduled tasks]
        for task in self.scheds:
            task = task.split("#")[0].strip()
            scrpt = task.split(';')[1].strip()
            notification = task.split(';')[2].strip()
            logging = task.split(';')[3].split("#")[0].strip()

            st = task.strip().split(';')[0].replace('@','').strip()

            if logging == '1':
                logging = True
            else:
                logging = False

            if self.recalc or not st in self.dates.keys():
        
                stries0 = list(set([st.replace('SS',x) for x in secs]))

                stries1 = []
                for stry in stries0:
                    stries1 += list(set([stry.replace('MM',x) for x in M]))

                stries2 = []
                for stry in stries1:
                    stries2 += list(set([stry.replace('HH',x) for x in H]))

                stries3 = []
                for stry in stries2:
                    stries3 += list(set([stry.replace('dd',x) for x in d]))

                stries4 = []
                for stry in stries3:
                    stries4 += list(set([stry.replace('mm',x) for x in m]))

                stries5 = []
                for stry in stries4:
                    stries5 += list(set([stry.replace('yyyy',x) for x in years]))

                stimes0 = []
                for stry in stries5:
                    try:
                        x = mktime(datetime.strptime(stry,"%Y.%m.%d.%H.%M:%S").timetuple())
                        dif = x - self.cts
                        stimes0 += [dif]
                    except ValueError:
                        pass

                stimes = [x for x in sorted(stimes0) if x >=0]
                sdate = ""

                if len(stimes0) == 0:
                    msg = "invalid time" + " "*5 + scrpt
                    self.dates[st] = ["invalid time",""]

                elif len(stimes) == 0:
                    msg = "complete" + " "*9 + scrpt
                    self.dates[st] = ["complete",""]

                else:
                    sts = stimes[0] + self.cts
                    sdate = str(datetime.fromtimestamp(sts).strftime("%Y.%m.%d.%H.%M:%S"))
                    self.dates[st] = [sts,sdate]

            
            sts = self.dates[st][0]
            sdate = self.dates[st][1]

            if sts == "invalid time":
                msg = "invalid time" + " "*5 + scrpt

            elif sts == "complete":
                msg = "complete" + " "*9 + scrpt

            else: 
                dd = (sts - self.cts)/(self.sid)
                dr = int(dd)
                
                hd = (dd - dr)*24
                hr = int(hd)

                md = (hd - hr)*60
                mr = int(md)

                sd = (md - mr)*60
                sr = self.rounder(sd)

                msg = str(dr).zfill(3) + "d " + str(hr).zfill(2) + "h " + str(mr).zfill(2) + "m " + str(sr).zfill(2) + "s " + scrpt

                if sr <= 0:
                    del self.dates[st]
                
                spath = self.scripts + scrpt
                if not spath in files_exist.keys():
                    files_exist[spath] = os.path.isfile(spath)

                if not(files_exist[spath]):
                    msg += " (Script Not Found)"

            msgs += [msg]

            if sdate == sct and self.pt != sct:

                if not(os.path.isfile(spath)):

                    ppmsg = scrpt + " failed!"

                    if notification == "1":
                        window_msgs += [ppmsg]
                    elif notification == "2" and self.in_tray:
                        tray_msgs += [ppmsg]

                    if self.do_log:
                        self.log = "[E] " + sct + " - " + scrpt + "\n" + self.log
                        added_log = True

                else:

                    if logging:
                        out_scrpt = self.output + scrpt
                        if not os.path.isdir(out_scrpt):
                            os.mkdir(out_scrpt)
                        output_temp = out_scrpt + "\\" + sdate.replace(":",".") +"_"+ str(time()) + ".txt"
                        cmd_logging = [">>",output_temp]
                    else:
                        cmd_logging = []

                    scrpt_ext = scrpt.split(".")[-1]
                    if scrpt_ext == "py":
                        command = [self.pypath, spath] + cmd_logging
                    elif scrpt_ext == "pyw":
                        command = [self.pywpath, spath] + cmd_logging
                    else:
                        command = [spath] + cmd_logging

                    # initiate the script
                    Popen(command, shell=True,stdin=None, stdout=None, stderr=None, close_fds=True)
                    if st in self.dates:
                        del self.dates[st]
     

                    ppmsg = scrpt + " initiated!"

                    if self.in_tray:
                         self.change_tray_icon(QIcon(self.support + r"blue_robot.png"))

                    if notification == "1":
                        window_msgs += [ppmsg]
                    elif notification == "2" and self.in_tray:
                        tray_msgs += [ppmsg]

                    if self.do_log:
                        self.log = "[S] " + sct + " - " + scrpt + "\n" + self.log
                        added_log = True

        # [end loop through the scheduled tasks]

        self.pt = sct
        
        if tray_msgs != []:
            self.show_tray_message("\n".join(tray_msgs))
        
        if window_msgs != []:
            self.show_message("\n".join(window_msgs))

        curr_msgs = "\n".join(msgs)
        if self.prev_msgs != curr_msgs:
            cpos = self.text_countdown.verticalScrollBar().value()
            self.text_countdown.setPlainText(curr_msgs)
            self.text_countdown.verticalScrollBar().setValue(cpos)
        self.prev_msgs = curr_msgs

        if self.do_log and added_log:
            cpos = self.text_log.verticalScrollBar().value()
            self.text_log.setPlainText(self.log + self.text_log.toPlainText())
            self.text_log.verticalScrollBar().setValue(cpos)
        

    def get_selection(self):
        cursor = self.text_editor.textCursor()
        return (cursor.selectionStart(),cursor.selectionEnd())

    def eventFilter(self,source,event):
        
        # for the checkboxes
        # right click context menu for opening file
        if event.type() == QEvent.ContextMenu and source in [self.gbts_dict[x] for x in self.gbts_dict]:
            menu = QMenu()
            menu.addAction('Open File')
            if menu.exec_(event.globalPos()):
                Popen(["notepad.exe", self.gbt + source.text()], shell=True,stdin=None, stdout=None, stderr=None, close_fds=True)

        # for the text editor keypresses
        # if keypress == Ctrl + /
        if (event.type() == QEvent.KeyPress and source is self.text_editor):
            modifiers = QApplication.keyboardModifiers()
            if modifiers == Qt.ControlModifier and event.key() == 47:

                rng = self.get_selection()
                txt = self.text_editor.toPlainText()
                slen = len(txt)
                splt = txt.split("\n")
                count = 0
                counts = []
                add = 0
                for i in splt:
                    count += len(i)
                    counts += [count+add]
                    add+=1
                    
                linesi = []
                for i in rng:
                    linesi += [counts.index(min([x for x in counts if x - i >= 0]))]

                wantlines = splt[linesi[0]:linesi[1]+1]
                wantlines2 = [x for x in wantlines if x.strip() != ""]
                if all([x.strip()[0] == "#" for x in wantlines2]):
                    remove = True
                else:
                    remove = False

                tolines = []
                for w in wantlines:
                    if w.strip() == "":
                        tolines += [w]
                    else:
                        if not remove:
                            tolines += ["# " + w]
                        else:
                            rp = w.replace("#","",1)
                            if rp[0] == " ":
                                rp = rp.replace(" ","",1)
                            tolines += [rp]
                rlines = []
                if linesi[0] != 0:
                    rlines += splt[:linesi[0]]
                rlines += tolines + splt[linesi[1]+1:]
                rtxt = "\n".join(rlines)

                flen = len(rtxt)
                self.text_editor.setPlainText(rtxt)
    
                cursor = self.text_editor.textCursor()
                
                if rng[0] == rng[1]:
                    cursor.setPosition(rng[0] + (flen-slen))
                    cursor.setPosition(rng[1] + (flen-slen), QTextCursor.KeepAnchor)
                else:
                    cursor.setPosition(rng[0])
                    cursor.setPosition(rng[1] + (flen-slen), QTextCursor.KeepAnchor)
                self.text_editor.setTextCursor(cursor)

                return 1


        return 0


    def tray_tool_tip(self):
        if self.in_tray:
            string = "GBot" + "\n" + str(self.task_count) + " task"
            if self.task_count != 1:
                string += "s"
            self.tray.setToolTip(string)
            


    def to_tray(self):

        self.in_tray = True

        self.hide()
        menu = QMenu()

        settingAction = menu.addAction("Show Window")
        settingAction.triggered.connect(self.show_window)

        exitAction = menu.addAction("Exit GBot")
        exitAction.triggered.connect(self.custom_close)

        self.tray = QSystemTrayIcon()
        self.tray.setIcon(self.main_icon)
        self.tray.setContextMenu(menu)
        self.tray.show()
        self.tray.setToolTip("GBot")
        if not self.was_tray:
            self.tray.showMessage("","I'm in your tray!")
        self.was_tray = True

    def read_tasks(self):
        self.path_mgmt(False)

        gbts1 = [x for x in self.gbts_dict2 if self.gbts_dict2[x] == 1]
        lines = []
        for gbt in gbts1:
            with open(self.gbt + gbt,'r') as f:
                lines += f.read().split("\n")

        lines += self.text_editor.toPlainText().split("\n")
        jlines = "\n".join(lines)
        self.recalc = False
        if self.prev_lines != jlines:
            self.recalc = True
            self.scheds = [self.is_valid(x) for x in lines]
            self.scheds = [x.strip() for x in self.scheds if x != None]
            self.task_count = len(self.scheds)
            self.text_tasks.setPlainText("\n".join(self.scheds))
            
        self.prev_lines = jlines

    def is_valid(self,string):
        if string.strip() != "":
            if string.strip()[0] != "#":
                if len(string.split(";")) == 4 and len(string.split(".")) >= 6 and len(string.split(":")) >= 2:
                    if len(string.strip()) > 22:
                        splt1 = string.strip().split(";")[0].strip()
                        if len(splt1) == 19:
                            if len(splt1.split(".")) == 5:
                                if len(splt1.split(":")) == 2:
                                    if len(splt1.split(".")[0]) == 4: #yyyy
                                        if len(splt1.split(".")[1]) == 2: #mm
                                            if len(splt1.split(".")[2]) == 2: #dd
                                                if len(splt1.split(".")[3]) == 2: #HH
                                                    if len(splt1.split(".")[4].split(":")[0]) == 2: #MM
                                                        if len(splt1.split(".")[4].split(":")[1]) == 2: #SS
                                                            return string

    def checked_gbt(self,int):
        gbt_file = self.sender().text()
        if int == 2:
            self.gbts_dict2[gbt_file] = 1
            self.change_status('Selected gbt file')
        else:
            self.gbts_dict2[gbt_file] = 0
            self.change_status('Unselected gbt file')

        self.select_history(update=True)

    def update_gbts(self):
        self.path_mgmt(False)
        ld = os.listdir(self.gbt)

        dgbts = [x for x in self.gbts_dict if not x in ld]

        for d in dgbts:
            self.gbts_dict[d].setParent(None)
            del self.gbts_dict[d]
            del self.gbts_dict2[d]

        gbts_new = [x for x in ld if ".gbt" in x.lower() and not(x in self.gbts_dict)]

        for gbt_new in gbts_new:
            self.gbts_dict[gbt_new] = QCheckBox(gbt_new,self)
            self.gbts_dict[gbt_new].setChecked(False)
            self.gbts_dict[gbt_new].stateChanged.connect(self.checked_gbt)
            self.chkBoxLayout.addWidget(self.gbts_dict[gbt_new])
            self.gbts_dict2[gbt_new] = 0
            self.gbts_dict[gbt_new].installEventFilter(self)
        
        self.widget.setLayout(self.grid)


    def change_tray_icon(self,ico):
        self.tray.setIcon(ico)
        self.timer_tray = QTimer()
        self.timer_tray.timeout.connect(self.change_tray_icon_back)
        self.timer_tray.start(4000)

    def change_tray_icon_back(self):
        self.tray.setIcon(self.main_icon)
        self.timer_tray.stop()


    def change_status(self,msg):
        self.statusbar.showMessage(msg)
        self.timer_status = QTimer()
        self.timer_status.timeout.connect(self.status_bar_ready)
        self.timer_status.start(2000)

    def status_bar_ready(self):
        self.statusbar.showMessage('Ready')
        self.timer_status.stop()


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def save_gbt(self):
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self,"Save",self.gbt,"Gbot Files (*.gbt);;All Files (*)", options=options)
        if fileName:
            with open(fileName,'w') as f:
                f.write(self.text_editor.toPlainText())

    def select_all_gbt(self):
        for gbt in self.gbts_dict:
            self.gbts_dict[gbt].setChecked(True)
            self.gbts_dict2[gbt] = 1
        self.change_status("Selected all gbt files")

    def unselect_all_gbt(self):
        for gbt in self.gbts_dict:
            self.gbts_dict[gbt].setChecked(False)
            self.gbts_dict2[gbt] = 0
        self.change_status("Unselected all gbt files")
        
    def edit_gbt(self):
        gbts = [x for x in self.gbts_dict2 if self.gbts_dict2[x] == 1]
        for gbt in gbts:
            sp = Popen(["notepad.exe", self.gbt + gbt], shell=True,stdin=None, stdout=None, stderr=None, close_fds=True)

    def clear_log(self):
        self.text_log.setPlainText("")
        self.log = ""

    def view_readme(self):
        sp = Popen(["notepad.exe", self.readme_path], shell=True,stdin=None, stdout=None, stderr=None, close_fds=True)

    def copy_tasks(self):
        import win32clipboard
        contents = self.text_tasks.toPlainText()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText(contents)
        win32clipboard.CloseClipboard()
    
    def show_message(self,_msg):
        self.gbot_msg = GBot_Message()
        self.gbot_msg.lbl1.setText(_msg)
        self.gbot_msg.show()


    def show_tray_message(self,_msg):
        self.tray.showMessage("",_msg)

    def preferences(self):
        self.pref = GBot_Preferences()
        self.pref.show()

    def build_menu(self):
        # create a menu bar
        menubar = self.menuBar()
        menubar.setStatusTip('Menu')
        fileMenu = menubar.addMenu('File')
        toolsMenu = menubar.addMenu('Tools')
        viewMenu = menubar.addMenu('View')

        # file menu stuff
        self.prefAct = QAction('Preferences', self)      
        self.prefAct.setStatusTip('Edit Preferences')
        self.prefAct.triggered.connect(self.preferences)

        self.saveAct = QAction('Save As', self)
        self.saveAct.setShortcut('Ctrl+S')       
        self.saveAct.setStatusTip('Save contents of the task editor')
        self.saveAct.triggered.connect(self.save_gbt)

        self.selectAct = QAction('Select All', self)        
        self.selectAct.setStatusTip('Select all gbt files')
        self.selectAct.triggered.connect(self.select_all_gbt)

        self.unselectAct = QAction('Unselect All', self)
        self.unselectAct.setStatusTip('Unselect all gbt files')
        self.unselectAct.triggered.connect(self.unselect_all_gbt)

        # self.exitAct = QAction(self.main_icon, 'Exit', self)
        self.exitAct = QAction('Exit', self)       
        self.exitAct.setShortcut('Ctrl+Q')
        self.exitAct.setStatusTip('Exit application')
        self.exitAct.triggered.connect(self.custom_close)

        # tools menu stuff
        self.copyAct = QAction('Copy Tasks', self)        
        self.copyAct.setStatusTip('Copy the contents of the task window to clipboard')
        self.copyAct.triggered.connect(self.copy_tasks)

        self.editAct = QAction('Edit Selected', self)        
        self.editAct.setStatusTip('Edit selected gbt files')
        self.editAct.triggered.connect(self.edit_gbt)

        self.clogAct = QAction('Clear Log', self)        
        self.clogAct.setStatusTip('Clear the log window')
        self.clogAct.triggered.connect(self.clear_log)

        self.logAct = QAction('Keep Log', self, checkable=True)
        self.logAct.setStatusTip('Toggle logging')
        self.logAct.setChecked(self.do_log)
        self.logAct.triggered.connect(self.toggleLog)

        # view menu stuff
        self.viewStatAct = QAction('View Statusbar', self, checkable=True)
        self.viewStatAct.setStatusTip('Toggle the statusbar')
        self.viewStatAct.setChecked(True)
        self.viewStatAct.triggered.connect(self.toggleMenu)

        self.readmeAct = QAction('README', self)        
        self.readmeAct.setStatusTip('View the README')
        self.readmeAct.triggered.connect(self.view_readme)
        
        # add actions to file menu
        fileMenu.addAction(self.prefAct)
        fileMenu.addAction(self.saveAct)
        fileMenu.addAction(self.selectAct)
        fileMenu.addAction(self.unselectAct)
        fileMenu.addAction(self.exitAct)
        
        # add actions to tools menu
        toolsMenu.addAction(self.copyAct)
        toolsMenu.addAction(self.editAct)
        toolsMenu.addAction(self.clogAct)
        toolsMenu.addAction(self.logAct)

        # add actions to view menu
        viewMenu.addAction(self.readmeAct)
        viewMenu.addAction(self.viewStatAct)
    
    def toggleLog(self,state):
        if state:
            self.do_log = True
        else:
            self.do_log = False

    def rounder(self,_number):
        if _number - int(_number) >= .5:
            return int(_number) + 1
        else:
            return int(_number)

    def toggleMenu(self, state):
        if state:
            self.statusbar.show()
        else:
            self.statusbar.hide()

    def select_history(self,update):
        import json

        if update:
            with open(self.select_path, 'w') as f:
                json.dump(self.gbts_dict2, f)

        elif not update and os.path.isfile(self.select_path):
            with open(self.select_path,'r') as f:
                    data = json.load(f)
            
            for i in data.keys():
                if i in self.gbts_dict2:
                    self.gbts_dict2[i] = data[i]
                    if data[i] == 0:
                        self.gbts_dict[i].setChecked(False)
                    else:
                        self.gbts_dict[i].setChecked(True)

            with open(self.select_path, 'w') as f:
                json.dump(self.gbts_dict2, f)



    def path_mgmt(self,update):
        import json
        # if updating paths
        if update:
            if self.gbt[-1] != "\\":
                self.gbt += "\\"
            if self.scripts[-1] != "\\":
                self.scripts += "\\"
            if self.output[-1] != "\\":
                self.output += "\\"

            data = {}
            data['gbt'] = self.gbt
            data['scripts'] = self.scripts
            data['output'] = self.output
            with open(self.paths, 'w') as f:
                json.dump(data, f)

        elif not update and os.path.isfile(self.paths):
            with open(self.paths,'r') as f:
                data = json.load(f)
            
            if 'gbt' in data.keys():
                self.gbt = data['gbt']
            else:
                self.gbt = self.appd + "gbt\\"
            if 'scripts' in data.keys():
                self.scripts = data['scripts']
            else:
                self.scipts = self.appd + "scripts\\"
            if 'output' in data.keys():
                self.output = data['output']
            else:
                self.output = self.appd + "output\\"

        else:
            self.output = self.appd + "output\\"
            self.gbt = self.appd + "gbt\\"
            self.scripts = self.appd + "scripts\\"

            data = {}
            data['gbt'] = self.gbt
            data['scripts'] = self.scripts
            data['output'] = self.output
            with open(self.paths, 'w') as f:
                json.dump(data, f)

        if not(os.path.isdir(self.gbt)):
            os.makedirs(self.gbt)
        if not(os.path.isdir(self.output)):
            os.makedirs(self.output)
        if not(os.path.isdir(self.scripts)):
            os.makedirs(self.scripts)


    def show_window(self):
        self.show()
        self.in_tray = False
        self.tray.hide()
    
    def custom_close(self):
        with open(self.appd_t,'w') as f:
            f.write(self.text_editor.toPlainText())
        try:
            self.tray.hide()
        except Exception as e:
            pass
        QCoreApplication.instance().quit()

    def closeEvent(self, event):

        if self.tray_app:
            self.to_tray()
            event.ignore()
        else:
            self.custom_close()


        
class FileEdit(QTextEdit):
    def __init__( self ):
        super().__init__()

    def dragEnterEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dragMoveEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            event.acceptProposedAction()

    def dropEvent( self, event ):
        data = event.mimeData()
        urls = data.urls()
        if urls and urls[0].scheme() == 'file':
            filepath = str(urls[0].path())[1:]
            if filepath.split(".")[-1].lower() in ["gbt","txt"]:
                try:
                    with open(filepath,'r') as f:
                        contents = f.read()
                except:
                    contents = ""
                
                self.setText(self.toPlainText()  + contents)

class GBot_Preferences(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()        
        
    def initUI(self):

        self.main_icon = gui.main_icon
        self.setFont(gui.font())
        self.setWindowTitle('GBot Preferences') 
        self.setWindowIcon(self.main_icon)

        self.lbl1 = QLabel('gbt path:', self)
        self.lbl2 = QLabel('scripts path:', self)
        self.lbl3 = QLabel('output path:', self)
        self.lbl4 = QLabel('font:', self)

        self.line_gbt = QLineEdit()
        self.line_gbt.setText(gui.gbt)
        self.line_scripts = QLineEdit()
        self.line_scripts.setText(gui.scripts)
        self.line_output = QLineEdit()
        self.line_output.setText(gui.output)

        self.comboBox = QComboBox(self)
        for font in gui.fonts:
            self.comboBox.addItem(font)
        index = self.comboBox.findText(gui.font_choice, Qt.MatchFixedString)
        if index >= 0:
            self.comboBox.setCurrentIndex(index)

        self.btn = QPushButton('Save', self)
        self.btn.clicked.connect(self.save_prefs)
        self.btn.setFixedSize(50,23)

        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        cspan = 3
        self.grid.addWidget(self.lbl1, 0, 0,1,cspan)
        self.grid.addWidget(self.line_gbt, 1, 0,1,cspan)
        self.grid.addWidget(self.lbl2, 2, 0,1,cspan)
        self.grid.addWidget(self.line_scripts, 3, 0,1,cspan)
        self.grid.addWidget(self.lbl3, 4, 0,1,cspan)
        self.grid.addWidget(self.line_output, 5, 0,1,cspan)
        self.grid.addWidget(self.lbl4, 6, 0,1,cspan)
        self.grid.addWidget(self.comboBox, 7, 0,1,1)
        self.grid.addWidget(self.btn, 8, 0,1,1)

        self.setLayout(self.grid)

        self.setGeometry(300, 300, 450, 200)

        self.show()
    
    def save_prefs(self):

        gbt = self.line_gbt.text()
        if gbt.strip() == "":
            return
        gui.gbt = gbt

        scripts = self.line_scripts.text()
        if scripts.strip() == "":
            return
        gui.scripts = scripts

        output = self.line_output.text()
        if output.strip() == "":
            return
        gui.output = output

        gui.font_choice = self.comboBox.currentText()
        gui.update_font(update=True)

        gui.path_mgmt(update=True)
        gui.change_status("Updated preferences")
        self.close()

        


class GBot_Message(QWidget):

    def __init__(self):
        super().__init__()
        self.initUI()        
        
    def initUI(self):

        self.main_icon = gui.main_icon
        self.setFont(gui.font())
        self.setWindowTitle('GBot Message') 
        self.setWindowIcon(self.main_icon)
        
        self.lbl1 = QLabel('', self)
        self.btn = QPushButton('Okay', self)
        self.btn.clicked.connect(self.okay)
        self.btn.setFixedSize(50,28)

        self.grid = QGridLayout()
        self.grid.setSpacing(5)

        self.grid.addWidget(self.lbl1, 0, 0)
        self.grid.addWidget(self.btn, 1, 0)

        self.setLayout(self.grid)

        self.setGeometry(300, 300, 200, 100)

        self.show()

    def okay(self):
        self.close()

# used for the log
class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent):
        super(Highlighter, self).__init__(parent)
        self.sectionFormat = QTextCharFormat()
        self.sectionFormat.setForeground(Qt.black)
        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(Qt.red)
    def highlightBlock(self, text):
        if text.startswith('[S]'):
            self.setFormat(0, len(text), self.sectionFormat)
        elif text.startswith('[E]'):
            self.setFormat(0, len(text), self.errorFormat)

# used for the countdown
class Highlighter2(QSyntaxHighlighter):
    def __init__(self, parent):
        super(Highlighter2, self).__init__(parent)
        self.sectionFormat = QTextCharFormat()
        self.sectionFormat.setForeground(Qt.black)
        self.errorFormat = QTextCharFormat()
        self.errorFormat.setForeground(Qt.red)
    def highlightBlock(self, text):
        if not "(Script Not Found)" in text:
            self.setFormat(0, len(text), self.sectionFormat)
        else:
            self.setFormat(0, len(text), self.errorFormat)
            
if __name__ == '__main__':

    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("gbot_gui_ctypes_thing")

    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(False)
    gui = GBot()
    gui.tray_app = True
    gui.build_menu()
    gui.show()
    app.exec_()

