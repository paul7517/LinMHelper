import tkinter as tk
from tkinter import ttk
import queue
from time import sleep
from tkinter import StringVar
from configparser import ConfigParser
from os import listdir
from fnmatch import filter
from santa.PlayerThread import PlayerThread
from santa.config import emulator_config
from santa.logger import log
from PIL.ImageTk import PhotoImage


# ====== 主題色彩 ======
COLORS = {
    'bg':           '#1e1e2e',
    'bg_card':      '#2a2a3d',
    'bg_card_alt':  '#252538',
    'bg_toolbar':   '#252538',
    'bg_header':    '#1a1a2a',
    'fg':           '#cdd6f4',
    'fg_dim':       '#6c7086',
    'fg_bright':    '#ffffff',
    'accent':       '#89b4fa',
    'accent_hover': '#b4d0fb',
    'green':        '#a6e3a1',
    'green_bg':     '#1e3a2f',
    'red':          '#f38ba8',
    'red_bg':       '#3a1e2c',
    'orange':       '#fab387',
    'yellow':       '#f9e2af',
    'border':       '#45475a',
    'input_bg':     '#313244',
    'input_fg':     '#cdd6f4',
}

FONT_FAMILY = 'Microsoft JhengHei UI'
FONT = (FONT_FAMILY, 10)
FONT_BOLD = (FONT_FAMILY, 10, 'bold')
FONT_SMALL = (FONT_FAMILY, 9)
FONT_TITLE = (FONT_FAMILY, 12, 'bold')
FONT_ICON = (FONT_FAMILY, 11)


class LinMHelperApp():
    threadCount = 4
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('LinM Helper')
        self.root.geometry('920x320')
        self.root.resizable(True, True)
        self.root.configure(bg=COLORS['bg'])
        self.root.minsize(700, 280)
        
        # 實例屬性
        self.config = ConfigParser()
        self.showIndex = -1
        self.wNameList = []
        self.wInfoList = []
        self.wProfileVarList = []
        self.wProfileList = []
        self.btnList = []
        self.wThreads = []
        self.phImage = None
        self.phLabel = None
        self._statusDots = []  # 狀態指示燈
        
        # Thread -> GUI 的通訊 queue
        self._gui_queue = queue.Queue()
        
        # ====== 設定 ttk 樣式 ======
        self._setup_styles()
        
        # ====== 頂部標題列 ======
        headerFrame = tk.Frame(self.root, bg=COLORS['bg_header'], height=40)
        headerFrame.pack(fill='x')
        headerFrame.pack_propagate(False)
        
        tk.Label(headerFrame, text='⚔', font=(FONT_FAMILY, 14), 
                 bg=COLORS['bg_header'], fg=COLORS['accent']).pack(side='left', padx=(12, 4))
        tk.Label(headerFrame, text='LinM Helper', font=FONT_TITLE,
                 bg=COLORS['bg_header'], fg=COLORS['fg_bright']).pack(side='left')
        tk.Label(headerFrame, text='v2.0', font=FONT_SMALL,
                 bg=COLORS['bg_header'], fg=COLORS['fg_dim']).pack(side='left', padx=(6, 0), pady=(3, 0))
        
        # 模板狀態（右上角）
        self._templateStatusLabel = tk.Label(headerFrame, text='', font=FONT_SMALL,
                                              bg=COLORS['bg_header'], fg=COLORS['fg_dim'])
        self._templateStatusLabel.pack(side='right', padx=12)
        
        # ====== 工具列 ======
        toolFrame = tk.Frame(self.root, bg=COLORS['bg_toolbar'], height=36)
        toolFrame.pack(fill='x')
        toolFrame.pack_propagate(False)
        
        # 世界王時段
        self.bossTimeList = ['12:00', '13:00', '19:00', '20:00', '21:00', '22:00']
        self.bossTimeVariable = []
        
        tk.Label(toolFrame, text='世界王', font=FONT_SMALL,
                 bg=COLORS['bg_toolbar'], fg=COLORS['fg_dim']).pack(side='left', padx=(12, 4))
        
        for i in range(6):
            self.bossTimeVariable.append(tk.IntVar())
            cb = tk.Checkbutton(toolFrame, text=self.bossTimeList[i],
                               variable=self.bossTimeVariable[i],
                               font=FONT_SMALL,
                               bg=COLORS['bg_toolbar'], fg=COLORS['fg'],
                               selectcolor=COLORS['input_bg'],
                               activebackground=COLORS['bg_toolbar'],
                               activeforeground=COLORS['fg'])
            cb.select()
            cb.pack(side='left', padx=1)
        
        # 分隔線
        sep = tk.Frame(toolFrame, width=1, bg=COLORS['border'])
        sep.pack(side='left', fill='y', padx=8, pady=6)
        
        self.hideWindowVar = tk.IntVar()
        tk.Checkbutton(toolFrame, text='隱藏視窗', variable=self.hideWindowVar,
                       font=FONT_SMALL,
                       bg=COLORS['bg_toolbar'], fg=COLORS['fg'],
                       selectcolor=COLORS['input_bg'],
                       activebackground=COLORS['bg_toolbar'],
                       activeforeground=COLORS['fg']).pack(side='left', padx=2)
        
        # 右側按鈕
        self._make_tool_button(toolFrame, '⏹ 全部停止', COLORS['red'], self._stop_all).pack(side='right', padx=(2, 12))
        self._make_tool_button(toolFrame, '📷 模板管理', COLORS['accent'], self._open_template_manager).pack(side='right', padx=2)
        
        # ====== 分隔線 ======
        tk.Frame(self.root, height=1, bg=COLORS['border']).pack(fill='x')
        
        # ====== 玩家列表區 ======
        self.playerFrame = tk.Frame(self.root, bg=COLORS['bg'])
        self.playerFrame.pack(fill='both', expand=True, padx=8, pady=6)
        
        self.loadConfig()
        
        # ====== 底部截圖預覽 ======
        self.phImage = tk.PhotoImage()
        self.phLabel = tk.Label(self.root, bg=COLORS['bg'])
        self.phLabel.pack()
        
        # 指定視窗關閉時的 handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # 啟動 GUI queue polling
        self._poll_gui_queue()
        self._refresh_template_status()
        
        self.root.mainloop()

    def _setup_styles(self):
        """設定 ttk 樣式"""
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('TFrame', background=COLORS['bg'])
        style.configure('Card.TFrame', background=COLORS['bg_card'])
        style.configure('TLabel', background=COLORS['bg'], foreground=COLORS['fg'], font=FONT)

    def _make_tool_button(self, parent, text, fg_color, command):
        """建立工具列按鈕"""
        btn = tk.Label(parent, text=text, font=FONT_SMALL,
                       bg=COLORS['bg_toolbar'], fg=fg_color,
                       cursor='hand2', padx=8)
        btn.bind('<Button-1>', lambda e: command())
        btn.bind('<Enter>', lambda e: btn.configure(fg=COLORS['fg_bright']))
        btn.bind('<Leave>', lambda e: btn.configure(fg=fg_color))
        return btn

    # ====== Thread-safe GUI 更新機制 ======
    
    def _poll_gui_queue(self):
        """定期從 queue 取出訊息並更新 GUI（在主線程執行）"""
        try:
            while True:
                msg = self._gui_queue.get_nowait()
                msg_type = msg[0]
                
                if msg_type == 'status':
                    _, i, text = msg
                    if 0 <= i < len(self.wInfoList):
                        self.wInfoList[i].configure(text=text, fg=COLORS['fg'])
                
                elif msg_type == 'image':
                    _, i, img = msg
                    if i == self.showIndex:
                        self.phImage = PhotoImage('RGBA', img.size)
                        self.phImage.paste(img)
                        self.phLabel.configure(image=self.phImage)
                
                elif msg_type == 'stop':
                    _, i = msg
                    if 0 <= i < len(self.btnList):
                        self._set_btn_stopped(i)
                        
        except queue.Empty:
            pass
        
        # 死線程偵測
        for i, t in enumerate(self.wThreads):
            if self.btnList[i]['text'] == '● 執行中' and not t.is_alive():
                self._set_btn_stopped(i)
                log.warning('Thread-%d 意外終止，已自動更新狀態', i)
        
        self.root.after(100, self._poll_gui_queue)
    
    def _on_status_update(self, i, text):
        self._gui_queue.put(('status', i, text))
    
    def _on_image_update(self, i, img):
        self._gui_queue.put(('image', i, img))
    
    def _get_running_state(self, i):
        if 0 <= i < len(self.btnList):
            return '執行中' in self.btnList[i]['text']
        return False
    
    def _get_hide_window(self):
        return self.hideWindowVar.get() == 1

    # ====== 產生玩家卡片 ======
    
    def newMonitor(self, i):
        bg = COLORS['bg_card'] if i % 2 == 0 else COLORS['bg_card_alt']
        
        card = tk.Frame(self.playerFrame, bg=bg, padx=8, pady=4)
        card.pack(fill='x', pady=1)
        
        # 序號標籤
        tk.Label(card, text=f'#{i+1}', font=FONT_BOLD, width=3,
                 bg=bg, fg=COLORS['accent']).pack(side='left')
        
        # 視窗名稱
        tk.Label(card, text='視窗', font=FONT_SMALL,
                 bg=bg, fg=COLORS['fg_dim']).pack(side='left', padx=(4, 2))
        
        wName = tk.Text(card, height=1, width=10, font=FONT,
                        bg=COLORS['input_bg'], fg=COLORS['input_fg'],
                        insertbackground=COLORS['fg'],
                        relief='flat', borderwidth=0, padx=4, pady=2)
        wName.pack(side='left', padx=2)
        self.wNameList.append(wName)
        
        # Profile 選單
        profileList = self.getIniList()
        selectVar = StringVar()
        selectVar.set('default.ini')
        self.wProfileVarList.append(selectVar)
        
        wProfile = tk.OptionMenu(card, selectVar, *profileList)
        wProfile.configure(font=FONT_SMALL, bg=COLORS['input_bg'], fg=COLORS['input_fg'],
                          activebackground=COLORS['accent'], activeforeground=COLORS['bg'],
                          relief='flat', borderwidth=0, highlightthickness=0)
        wProfile.pack(side='left', padx=4)
        self.wProfileList.append(wProfile)
        
        # 狀態文字
        wInfo = tk.Label(card, text='等待中...', font=FONT_SMALL, anchor='w',
                         bg=bg, fg=COLORS['fg_dim'])
        wInfo.bind('<Button-1>', lambda event: self.changeShowIndex(event, i))
        wInfo.pack(side='left', fill='x', expand=True, padx=8)
        self.wInfoList.append(wInfo)
        
        # 執行按鈕
        btnToggle = tk.Label(card, text='○ 已停止', font=FONT_BOLD, width=9,
                              bg=COLORS['input_bg'], fg=COLORS['fg_dim'],
                              cursor='hand2', padx=6, pady=2, relief='flat')
        btnToggle.bind('<Button-1>', lambda e, idx=i: self.toggle_it(idx))
        btnToggle.pack(side='right', padx=2)
        self.btnList.append(btnToggle)
        
        # 建立 PlayerThread
        pThread = PlayerThread(
            i, self,
            on_status_update=self._on_status_update,
            on_image_update=self._on_image_update,
            get_running_state=self._get_running_state,
            get_hide_window=self._get_hide_window,
        )
        self.wThreads.append(pThread)
    
    def _set_btn_running(self, i):
        self.btnList[i].configure(text='● 執行中', fg=COLORS['green'], bg=COLORS['green_bg'])
    
    def _set_btn_stopped(self, i):
        self.btnList[i].configure(text='○ 已停止', fg=COLORS['fg_dim'], bg=COLORS['input_bg'])

    # ====== 執行中/已停止的切換 ======
    
    def toggle_it(self, i):
        btnText = self.btnList[i]['text']
        if '已停止' in btnText: 
            self._set_btn_running(i)
            
            while self.wThreads[i].is_alive():
                log.info('正在等待Thread-%d停止。', i)
                sleep(2)
            
            self.wThreads[i] = PlayerThread(
                i, self,
                on_status_update=self._on_status_update,
                on_image_update=self._on_image_update,
                get_running_state=self._get_running_state,
                get_hide_window=self._get_hide_window,
            )
            self.wThreads[i].start()
        else:
            self._set_btn_stopped(i)
    
    # ====== 載入設定 ======
    
    def loadConfig(self):
        for i in range(self.threadCount):
            self.newMonitor(i)

        self.config.read('Main.ini')
        emulator_config.load_from_ini('Main.ini')
        iniList = self.getIniList()
        
        for i in range(self.threadCount):            
            in_wName = self.config['Player' + str(i)]['windowName']
            in_pName = self.config['Player' + str(i)]['profileName']
            in_enabled = self.config['Player' + str(i)]['enabled']
            
            self.wNameList[i].insert("1.0", in_wName)
            
            if in_pName in iniList:
                self.wProfileVarList[i].set(in_pName)

    # ====== 儲存設定並關閉 ======
    
    def on_closing(self):
        for i in range(self.threadCount):
            self.config['Player' + str(i)]['windowName'] = self.wNameList[i].get('1.0', 'end-1c')
            self.config['Player' + str(i)]['profileName'] = self.wProfileVarList[i].get()
            if '執行中' in self.btnList[i]['text']: 
                self.config['Player' + str(i)]['enabled'] = '1'
            else: 
                self.config['Player' + str(i)]['enabled'] = '0'
        
        emulator_config.save_defaults_to_ini(self.config)
        
        import os
        import tempfile
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', dir='.', suffix='.tmp', delete=False) as tmpfile:
                self.config.write(tmpfile)
                tmpName = tmpfile.name
            
            if os.path.exists('Main.old.ini'):
                os.remove('Main.old.ini')
            if os.path.exists('Main.ini'):
                os.rename('Main.ini', 'Main.old.ini')
            
            os.rename(tmpName, 'Main.ini')
        except Exception as e:
            log.error('儲存設定檔失敗: %s', e)
        
        for i in range(self.threadCount):
            self._set_btn_stopped(i)
        
        import time
        deadline = time.time() + 5
        for t in self.wThreads:
            while t.is_alive() and time.time() < deadline:
                sleep(0.5)
            
        self.root.destroy()
    
    def getIniList(self):
        inis = filter(listdir('./profile/'), '*.ini')
        return inis
    
    def changeShowIndex(self, event, i):
        if i == self.showIndex:
            self.showIndex = -1
        else:
            self.showIndex = i
    
    def _open_template_manager(self):
        import threading
        
        live_name = None
        for wNameWidget in self.wNameList:
            name = wNameWidget.get("1.0", "end-1c").strip()
            if name:
                live_name = name
                break
        
        if live_name is None:
            log.warning('沒有任何視窗名稱，無法開啟模板管理')
            return
        
        def _run():
            from santa.capture_templates import review_templates
            review_templates(live_wName=live_name)
            self.root.after(100, self._refresh_template_status)
        
        t = threading.Thread(target=_run, daemon=True)
        t.start()
    
    def _refresh_template_status(self):
        import os
        template_dir = os.path.join(os.path.dirname(__file__), 'templates')
        names = ['team_enabled', 'panel_opened', 'is_attack', 'is_attacked']
        found = sum(1 for n in names if os.path.exists(os.path.join(template_dir, f'{n}.png')))
        total = len(names)
        
        if found == total:
            text = f'✅ 模板 {found}/{total}'
            color = COLORS['green']
        elif found > 0:
            text = f'⚠ 模板 {found}/{total}'
            color = COLORS['orange']
        else:
            text = '○ 像素模式'
            color = COLORS['fg_dim']
        
        self._templateStatusLabel.configure(text=text, fg=color)
    
    def _stop_all(self):
        for i in range(self.threadCount):
            if '執行中' in self.btnList[i]['text']:
                self._set_btn_stopped(i)
        log.info('已停止所有 thread')
