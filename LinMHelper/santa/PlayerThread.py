from santa.Lib32 import FindWindow_bySearch, getWindow_Img, getControlID,\
    postMessage, getWindow_W_H, setWindowPosition
from _datetime import datetime, timedelta
from PIL.ImageTk import PhotoImage
from santa.ImageUtils import detectTeamEnabled, detectItemSkillPanelOpened, \
    detectHPPercent, detectMPPercent, detectIsAttack, detectIsAttacked,\
    detectTeamPositionAvalible
from threading import Thread
from configparser import ConfigParser
from time import sleep,strftime
from os import mkdir,path,popen
from winsound import Beep
from calendar import weekday
from santa.Lib32.keyPos import LinMKeySet

class PlayerThread(Thread):
    # 取得config 檔
    profileConfig = ConfigParser()
    img = None
    beforeMinutes = 5
    
    def __init__(self, i , tkObj):
        super(PlayerThread, self).__init__()
        self.stopped = False
        self.i = i
        self.tkObj = tkObj
        self.wNameText = tkObj.wNameList[i]
        self.wProfileVar = tkObj.wProfileVarList[i]
        self.wInfoLabel = tkObj.wInfoList[i]
        self.wBtn = tkObj.btnList[i]
        print('thread-%d Initialize' % i)
    
    def run(self):
        wName = self.wNameText.get("1.0", "end-1c")
        wProfile = self.wProfileVar.get()
        self.loadProfile(wProfile)
        
        hwnd = FindWindow_bySearch(wName)
        if(hwnd == None):
            print('Thead-%d: window title [%s] not found.' % (self.i , wName))
            self.wBtn['text'] = '已停止'
            return
        
        print('Thread-%d:wName=%s,HWND=%d,profileName=%s' % (self.i, wName, hwnd, wProfile))
        
        lastHomeTeleport = datetime.now()
        lastRndTeleport = datetime.now()
        sleepTime = 1
        
        # init config        
        teamPosition = self.readIntFromConfig('Common', 'TeamPosition') 
        hpCure = self.readIntFromConfig('Thresholds', 'HpCure') 
        mpTransHP = self.readIntFromConfig('Thresholds', 'MpTransHP')
        mpProtect = self.readIntFromConfig('Thresholds', 'MpProtect')
        hpBackHome = self.readIntFromConfig('Thresholds', 'HpBackHome')
        
        role = self.readStrFromConfig('Common', 'Role')
        backHomeKey = self.readStrFromConfig('Hotkey', 'BackHomeKey') 
        teleportKey = self.readStrFromConfig('Hotkey', 'TeleportKey') 
        cureKey = self.readStrFromConfig('Hotkey', 'CureKey')
        transHpKey = self.readStrFromConfig('Hotkey', 'TransHpKey')
        majorAttackKey = self.readStrFromConfig('Hotkey', 'MajorAttackKey')
        minorAttackKey = self.readStrFromConfig('Hotkey', 'MinorAttackKey')
        
        #用來紀錄非攻擊狀態的次數
        notAttackCnt = 0
        notAttackAlertTimes = 30

        #用來記錄畫面是否變灰及變暗
        darkCnt = 0
        
        while True:
            if(self.wBtn['text'] == '已停止'):
                break
            else:
                # 預設1 round的sleep秒數，後面會隨施放技能不同而改變
                sleep(sleepTime)

            now = datetime.now()
            
            #判斷是不是世界王時段，若是，執行世界王腳本
            runBoss , weekDay , idx = self.isRunBoss()
            if runBoss:
                self.bossQuestRun(hwnd,wName,backHomeKey,weekDay,idx)
                #10分鐘內都不再按回捲，避免世界王副本被暈到誤飛
                lastHomeTeleport = now + timedelta(minutes = 10)
            
            #判斷隱藏遊戲視窗要叫出或是隱藏
            self.hideOrShowWindow(hwnd)
                
            # 取得視窗的截圖
            self.img = getWindow_Img(hwnd)
            if(self.img == None):
                continue                
            #self.saveImage(self.img, wName, 'debug')
            
            hp = -1
            mp = -1
            infoToLabel = ""
            isTeamEnabled , isGrey = detectTeamEnabled(self.img)
            isRightPanelOpened = detectItemSkillPanelOpened(self.img)
            # print('PanelOpened = %r' %isRightPanelOpened)  
            
            if isGrey > 0:
                if isGrey == 2: #情境:對話確認視窗    
                    darkCnt += 1                                
                elif isGrey == 1:#情況: 對話中，但無確認視窗
                    self.doBeep(1)
                    self.logToConsole(f'[Beta][{wName}]可能是任務完成，無確認視窗按任意鍵繼續(預設攻擊鍵)。')
                    self.pressKey(hwnd,wName,majorAttackKey)

                if darkCnt == 5:
                    self.doBeep(1)
                    darkCnt = 0
                    self.logToConsole(f'[Beta][{wName}]可能是任務完成，並且在確認視窗(按確認鈕)。')      
                    self.pressKey(hwnd,wName,LinMKeySet.acceptQuest)               
                
                #實際上大概是2秒(加上pressKey約1秒)
                sleepTime = 2
                #迴圈重來
                continue
            else:
                darkCnt = 0 

            #如果超過次數沒有偵測到攻擊，發出聲響。
            if(notAttackCnt >= notAttackAlertTimes):
                self.doBeep(8)
                self.logToConsole(f'{wName}-超過{notAttackCnt}秒沒有偵測到攻擊，發出聲音。')                    

                notAttackAlertTimes = 300 if notAttackAlertTimes == 30 else notAttackAlertTimes * 2
            
            if(not(isTeamEnabled and not isRightPanelOpened)):
                if(not isTeamEnabled): infoToLabel = "無法偵測組隊狀態"
                if(isRightPanelOpened): infoToLabel = "道具或技能欄打開"
                infoToLabel = infoToLabel + "暫不動作。"
                notAttackCnt += 1
                sleepTime = 2
                #self.doBeep(1)
            else:
                if(detectTeamPositionAvalible(self.img, teamPosition)):
                    hp = detectHPPercent(self.img, teamPosition,255)
                    mp = detectMPPercent(self.img, teamPosition,255)
                elif(detectTeamPositionAvalible(self.img, 0)):                    
                    hp = detectHPPercent(self.img, 0,255)
                    mp = detectMPPercent(self.img, 0,255)
                
                    
                isAttack = detectIsAttack(self.img)
                isAttacked = detectIsAttacked(self.img)
                infoToLabel += "戰鬥狀態:%r," % isAttack
                
                if not isAttack:
                    notAttackCnt += 1
                else:
                    notAttackCnt = 0
                    notAttackAlertTimes=30
                
                # 血量夠低且距離上次回捲超過30秒才飛
                if (hp < hpBackHome and hp > 0 and (now - lastHomeTeleport).seconds >= 30): 
                    self.pressKey(hwnd,wName,backHomeKey)
                    self.saveImage(self.img, wName, "血低");  # 可能是被殺，存圖。
                    infoToLabel += "點擊回捲。"
                    
                    #特殊狀況，輸出至console
                    self.logToConsole(infoToLabel)
                    
                    lastHomeTeleport = now
                    self.doBeep(5) # 回村響5聲

                    sleepTime = 1
                elif( isAttacked and (now - lastRndTeleport).seconds >= 3 and (now - lastHomeTeleport).seconds >= 5):
                    # 被打，點瞬捲(3秒內不連飛，5秒內點過回捲也不飛，避免回村後再飛一次)
                    # 當組隊情況時teamPosition > 0 (假定人顧在旁邊)，被打不自動飛
                    self.pressKey(hwnd,wName,teleportKey)
                    self.saveImage(self.img, wName, "被打");
                    infoToLabel += "被打囉。"
                    
                    #特殊狀況，輸出至console
                    self.logToConsole(infoToLabel)
                    
                    lastRndTeleport = now
                    self.doBeep(3); # 被打響3聲
                    sleepTime = 1
                elif(hp < hpCure and hp > 0 and mp > 5):
                    sleepTime = 0 #加上執行延遲0.6秒
                    self.pressKey(hwnd,wName,cureKey)
                    infoToLabel += "施放治癒魔法。"
                elif(mp >= mpProtect and isAttack):
                    sleepTime = 0.4 #加上執行延遲0.6秒
                    self.pressKey(hwnd,wName,majorAttackKey)
                    infoToLabel += "施放攻擊魔法。"
                elif(not isAttack and mp < 90 and role == 'ELF' and mp >= 0):
                    sleepTime = 1.4 #加上執行延遲0.6秒
                    self.pressKey(hwnd,wName,transHpKey)
                    infoToLabel += "MP<90%，施放魂體轉換。"
                elif(mp < mpProtect and mp < 90 and hp >= mpTransHP):
                    sleepTime = 1.4 #加上執行延遲0.6秒
                    self.pressKey(hwnd,wName,transHpKey)
                    infoToLabel += "施放魂體轉換。"
                else:
                    infoToLabel += "啥也不做。"
                    sleepTime = 2
            
            endTime = datetime.now()
            executeTime = (endTime - now).microseconds / 1000
            
            infoToLabel = 'HP:%03d，MP:%03d，共執行%d毫秒，' % (hp, mp, executeTime) + infoToLabel
            
            # 若是選擇的thread，把圖輸出至GUI上
            if(self.i == self.tkObj.showIndex):
                self.tkObj.phImage = PhotoImage('RGBA', self.img.size)
                self.tkObj.phImage.paste(self.img)
                self.tkObj.phLabel.configure(image=self.tkObj.phImage)
            
            self.outputToLabel(infoToLabel)
            # self.saveImage(self.img,wName, '一般')
        
        self.stopped = True
        self.outputToLabel('已停止偵測。')
        print('Thread-%d Stoped' % self.i)
    
    def loadProfile(self, configFile):
        self.profileConfig.read('profile/' + configFile)

    # 輸出訊息至GUI介面          
    def outputToLabel(self, str):
        self.wInfoLabel.configure(text=str)
     
    # 以下三個副程式讀profile檔的內容及指定格式   
    def readFromConfig(self, sector, key):
        return self.profileConfig[sector][key]    

    def readStrFromConfig(self, sector, key):
            return str(self.readFromConfig(sector, key))

    def readIntFromConfig(self, sector, key):
            return int(self.readFromConfig(sector, key))

# 存圖
    def saveImage(self, img, wName, imgType):
        if(not (path.exists("LinMOut") )):
            mkdir("LinMOut")
        nowStr = strftime('%Y%m%d-%H-%M-%S.png')
        imgName = 'LinMOut/' + wName + "_" + imgType + '_' + nowStr
        img.save(imgName, "PNG")

       
    def pressKey(self,hwnd,wName,key):
        #postMessage(hwnd, key)
        self.adb_tap(wName , key)
        #self.tkObj.q.put((hwnd,key))
    
    
    def adb_tap(self,wName,pos):
        keyDict = {'1' : LinMKeySet.key1,
            '2' : LinMKeySet.key2,
            '3' : LinMKeySet.key3,
            '4' : LinMKeySet.key4,
            '5' : LinMKeySet.key5,
            '6' : LinMKeySet.key6,
            '7' : LinMKeySet.key7,
            '8' : LinMKeySet.key8}

        if not isinstance(pos , LinMKeySet) and pos in keyDict:
            pos = keyDict[pos]

        if isinstance(pos , LinMKeySet) and pos is not None:
            x , y = pos.value[0] , pos.value[1]
            execCmd = f'd: & cd "D:\\Program Files\\Nox\\bin\\" & .\\NoxConsole.exe adb -name:{wName} -command:"shell input tap {x} {y}"' 
            p = popen(execCmd)

            rst = p.readline()
            if rst[0:5] == 'error':
                print(f'error:{rst}')
                
                ipAddr = rst.split("'")[1]
                print(f'reconnect to {ipAddr}')                
                reconnectCmd = f'd: & cd "D:\\Program Files\\Nox\\bin\\" & .\\nox_adb.exe connect {ipAddr}'
                p = popen(reconnectCmd)
                print(p.readline())

        else:
            print(f'adb_tap input error {pos}')
    
    def doBeep(self , cnt):
        t=Thread(target=self.beep,args=(cnt,))
        t.start()
    
    def beep(self,cnt):
        for i in range(cnt):
            Beep(1500, 100)
            sleep(0.1)

    def logToConsole(self,msg):
        output = datetime.now().strftime('[%Y/%m/%d %H:%M:%S] ')
        output += msg
        print(output)
        
    def bossQuestRun(self,hwnd,wName,backHomeKey,weekDay,idx):
        print('進入副本腳本，先按回捲。') 
        self.pressKey(hwnd,wName,backHomeKey)        
        print('避免村莊lag，等個 5sec')
        sleep(5)
        
        print('點擊世界王按鈕(請設為0熱鍵)')
        #週一~週四及週六晚上10點的場次(底比斯) 及 週五、六晚上9點的場次(拉斯塔巴德hot-time)
        #按鈕位置左移80 px
        #if (weekDay in [0,1,2,3,5] and idx == 5) or (weekDay == 4 and idx == 4):
        if weekDay in [0,1,2,3,4,5] and idx == 5:
            self.pressKey(hwnd,wName, LinMKeySet.bossQuest2)
        else:
            self.pressKey(hwnd,wName, LinMKeySet.bossQuest)
        sleep(2)
        print('點擊確認')
        self.pressKey(hwnd,wName, LinMKeySet.key2)
        
        print('等待世界王開始')
        while(True):
            sleep(10)
            min =int(datetime.now().strftime('%M'))
            if(min == 0):
                self.pressKey(hwnd,wName,LinMKeySet.autoBtn)
                break
            
        print('開始打王！結束腳本')

    def isRunBoss(self):
        now = datetime.now()

        m = int(now.strftime('%M'))
        s = int(now.strftime('%S'))
        weekDay = now.weekday()
        runBoss = 0
        
        if(m == (60 - self.beforeMinutes) and 5 <= s <= 10):
            nextBossTimeStr = (now + timedelta(minutes = self.beforeMinutes)).strftime('%H:%M')           
            try:
                idx = self.tkObj.bossTimeList.index(nextBossTimeStr) #檢查是否為世界王時段
                runBoss = self.tkObj.bossTimeVariable[idx].get() #檢查checkbox
                
                #週日19:00、20:00場次沒開
                if idx in [2,3] and weekDay == 6:
                    runBoss = 0
            except:
                    runBoss = 0
        
        if runBoss == 0:
            return False , None , None
        else:
            return True , weekDay , idx
    
    #判斷遊戲視窗要隱藏或顯示
    def hideOrShowWindow(self,hwnd):
        x,y,width,height = getWindow_W_H(hwnd)
        #print(x,',',y)
        isHideWindow = self.tkObj.hideWindowVar.get()
        if(isHideWindow == 1 and x <= 8000 and y <= 8000):
            #設定X、Y至 > 10,000
            setWindowPosition(hwnd, x+10000, y+10000, width, height)
        elif isHideWindow == 0 and x >= 8000 and y>=8000:
            #設定X、Y至 < 10,000
            setWindowPosition(hwnd, x-10000, y-10000, width, height)

    