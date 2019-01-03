import tkinter as tk
from time import sleep
from tkinter import StringVar
from configparser import ConfigParser
from os import listdir
from shutil import move
from fnmatch import filter
from santa.PlayerThread import PlayerThread

class LinMHelperApp():
    threadCount = 4
    config = ConfigParser()
    showIndex = -1
    
    #前景物件
    wNameList = []
    wInfoList = []
    wProfileVarList = []
    wProfileList = []
    btnList = []
    phImage = None
    phLabel = None
    
    #背景使用
    wThreads = []
    
    #視窗初始化
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("1000x800")
        
        #self.q = queue.Queue()
        #self.q_listen = KeySender(self.q)
        #self.q_listen.start()

        #root.bind('<Escape>', lambda e: self.root.destroy())        
        #self.newFrame()
        
        self.bossTimeList = ['13:00' , '19:00' , '20:00' , '21:00' , '22:00' , '23:00']
        self.bossTimeVariable = []
        timeFrame = tk.Frame(self.root)
        timeFrame.anchor('w')
        timeFrame.pack()
        
        tk.Label(timeFrame,text = '自動世界王時段:').grid(row = 1,column = 1)
        
        for i in range(6):
            self.bossTimeVariable.append(tk.IntVar())
            checker = tk.Checkbutton(timeFrame,text = self.bossTimeList[i] , variable = self.bossTimeVariable[i])
            if i in [0,1,3]:
                checker.select()
            checker.grid(row = 1 , column = i+2)
        
        self.loadConfig()
        
        self.hideWindowVar = tk.IntVar()
        self.hideGameWindows = tk.Checkbutton(text='隱藏遊戲視窗。',variable = self.hideWindowVar)
        self.hideGameWindows.pack()
        
        self.phImage = tk.PhotoImage()
        self.phLabel = tk.Label()
        self.phLabel.pack()
        
        #指定視窗關閉時的handler
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    #暫時用不到
    '''
    def newFrame(self):
        frame=tk.Frame(self.root)
        btn = tk.Button(frame,text='新增掛機',command=self.newMonitor)
        btn.pack()
        frame.pack()
    '''
        
    #產生設定列
    def newMonitor(self,i):
        frame=tk.Frame(self.root)
        frame.anchor('w')
        
        #產生「視窗名稱」前置的Label
        wNameLbl = tk.Label(frame,text='視窗名稱')
        wNameLbl.grid(row=0,column=0)
        
        #產生「視窗名稱」輸入框
        wName = tk.Text(frame,height=1,width=15)
        wName.grid(row=0,column=1)
        self.wNameList.append(wName)
        
        #產生「角色狀態」資訊欄
        wInfo = tk.Label(frame,text='尚未開始偵測' ,width=80)
        wInfo.bind('<Button-1>', lambda event: self.changeShowIndex(event , i))
        wInfo.grid(row=0,column=2)
        self.wInfoList.append(wInfo)
        
        #產生profile下拉選單
        profileList = self.getIniList()
        selectVar = StringVar()
        selectVar.set('default.ini')
        self.wProfileVarList.append(selectVar)
        
        wProfile = tk.OptionMenu(frame,selectVar,*profileList)
        wProfile.grid(row=0,column=3)
        self.wProfileList.append(wProfile)
        
        #產生「執行中」、「已停止」按鈕
        btnToggle = tk.Button(frame,text='已停止',command=(lambda: self.toggle_it(i)))
        btnToggle.grid(row=0,column=4)
        self.btnList.append(btnToggle)
        #info.pack()
        frame.pack()
        
        #產出角色監看的執行緒
        pThread = PlayerThread(i,self)
        self.wThreads.append(pThread)
    
    #執行中/已停止的切換按鈕
    def toggle_it(self,i):
        btnText = self.btnList[i]['text']
        if(btnText == '已停止'): 
            self.btnList[i]['text']='執行中'
            
            while self.wThreads[i].isAlive():
                print('正在等待Thread-%d停止。' % i)
                sleep(2)
            
            self.wThreads[i] = PlayerThread(i,self)
            self.wThreads[i].start()
            
            #self.wThreads[i].start()
        else: self.btnList[i]['text']='已停止'
        #txt.master.destroy()
    
    #開始程式時，載入main.ini設定檔。
    #主要放置角色Nox Title、要讀哪一個profile檔 
    def loadConfig(self):
        #預設可以{threadCount)開，產出四行設定列
        for i in range(self.threadCount):
            self.newMonitor(i)

        self.config.read('Main.ini')
        #print(config.sections())
        
        iniList = self.getIniList()
        
        for i in range(self.threadCount):            
            in_wName = self.config['Player' + str(i)]['windowName']
            in_pName = self.config['Player' + str(i)]['profileName']
            in_enabled = self.config['Player' + str(i)]['enabled']
            
            self.wNameList[i].insert("1.0",in_wName)
            
            if(in_pName in iniList):
                self.wProfileVarList[i].set(in_pName)
            
            ''' 20181122發現自動啟動Thread似乎會錯序，先手動執行
            if(in_enabled=='1'): 
                self.btnList[i]['text'] ='執行中'
                self.wThreads[i].start()
            else: self.btnList[i]['text']='已停止'
            '''

    #當視窗關閉時，一併儲存main.ini檔
    def on_closing(self):
        for i in range(self.threadCount):
            self.config['Player' + str(i)]['windowName']=self.wNameList[i].get('1.0','end-1c')
            self.config['Player' + str(i)]['profileName']=self.wProfileVarList[i].get()
            if(self.btnList[i]['text'] =='執行中'): 
                self.config['Player' + str(i)]['enabled']='1'
            else: 
                self.config['Player' + str(i)]['enabled']='0'
        
        move('Main.ini','Main.old.ini')
        with open('Main.ini','w') as configfile:
            self.config.write(configfile)
            
        for t in self.wThreads:
            while not t.stopped:
                print('正在等待Thread停止')
                sleep(2)
                break
            
        self.root.destroy()
    
    #載入目前有哪些profile檔(將main.ini*排除)
    def getIniList(self):
        inis = filter(listdir('./profile/'), '*.ini')
        #print(inis)
        return inis
    
    def changeShowIndex(self,event,i):
        if(i == self.showIndex):
            self.showIndex = -1
        else:
            self.showIndex = i          