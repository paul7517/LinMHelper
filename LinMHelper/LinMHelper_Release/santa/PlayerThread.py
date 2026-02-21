from santa.Lib32 import FindWindow_bySearch, getWindow_Img, getControlID,\
    postMessage, getWindow_W_H, setWindowPosition
from datetime import datetime, timedelta
from PIL.ImageTk import PhotoImage
from santa.ImageUtils import detectTeamEnabled, detectItemSkillPanelOpened, \
    detectHPPercent, detectMPPercent, detectIsAttack, detectIsAttacked,\
    detectTeamPositionAvalible, drawSquares
from threading import Thread
from configparser import ConfigParser
from time import sleep,strftime
from os import mkdir,path
import subprocess
from winsound import Beep
from calendar import weekday
from santa.Lib32.keyPos import LinMKeySet, scale_pos, BASE_WIDTH, BASE_HEIGHT
from santa.config import emulator_config
from santa.logger import log
import random
from typing import Optional, Callable, Dict, Any, Tuple


class PlayerThread(Thread):
    beforeMinutes = 5
    
    def __init__(self, i: int, tkObj, on_status_update: Optional[Callable] = None,
                 on_image_update: Optional[Callable] = None, 
                 get_running_state: Optional[Callable] = None,
                 get_hide_window: Optional[Callable] = None,
                 get_boss_config: Optional[Callable] = None):
        super(PlayerThread, self).__init__(name=f'Player-{i}')
        self.daemon = True
        self.profileConfig = ConfigParser()
        self.stopped = False
        self.i = i
        self.tkObj = tkObj  # 保留向後相容，但盡量不直接操作
        self.img = None
        
        # callback 函數，由 GUI 層注入
        self._on_status_update = on_status_update  # fn(i, text)
        self._on_image_update = on_image_update    # fn(i, img)
        self._get_running_state = get_running_state  # fn(i) -> bool
        self._get_hide_window = get_hide_window    # fn() -> bool
        self._get_boss_config = get_boss_config    # fn() -> (bossTimeList, bossTimeVariable)
        
        # 從 tkinter widget 讀取初始值（只在主線程建立時讀一次）
        self._wName = tkObj.wNameList[i].get("1.0", "end-1c")
        self._wProfile = tkObj.wProfileVarList[i].get()
        
        log.info('Thread-%d 初始化完成', i)

    # ====== 狀態查詢（透過 callback 或 fallback 到直接讀取） ======
    
    def _is_running(self) -> bool:
        """檢查是否應繼續執行"""
        if self._get_running_state:
            return self._get_running_state(self.i)
        # fallback: 直接讀 button（不安全但向後相容）
        return self.tkObj.btnList[self.i]['text'] == '執行中'
    
    def _update_status(self, text: str) -> None:
        """更新狀態文字到 GUI"""
        if self._on_status_update:
            self._on_status_update(self.i, text)
        else:
            self.tkObj.wInfoList[self.i].configure(text=text)
    
    def _update_image(self, img) -> None:
        """更新截圖到 GUI"""
        if self._on_image_update:
            self._on_image_update(self.i, img)
    
    def _should_hide_window(self) -> bool:
        """取得隱藏視窗設定"""
        if self._get_hide_window:
            return self._get_hide_window()
        return self.tkObj.hideWindowVar.get() == 1

    # ====== 主要流程 ======
    
    def run(self):
        ctx = self._init_session()
        if ctx is None:
            return
        
        try:
            while self._is_running():
                sleep(ctx['sleepTime'])
                self._tick(ctx)
        except Exception as e:
            log.error('Thread-%d 意外崩潰: %s', self.i, e, exc_info=True)
            self._update_status('❗ 執行錯誤: %s' % str(e)[:50])
            # 通知 GUI 將按鈕設為停止
            if self._on_status_update:
                try:
                    self.tkObj._gui_queue.put(('stop', self.i))
                except Exception:
                    pass
        
        self.stopped = True
        self._update_status('已停止偵測。')
        log.info('Thread-%d 已停止', self.i)

    def _init_session(self) -> Optional[Dict[str, Any]]:
        """初始化掛機工作階段，回傳 context dict 或 None"""
        self.loadProfile(self._wProfile)
        wName = self._wName
        
        hwnd = FindWindow_bySearch(wName)
        if hwnd is None:
            log.warning('Thread-%d: 找不到視窗 [%s]', self.i, wName)
            self._update_status('找不到視窗 [%s]' % wName)
            return None
        
        log.info('Thread-%d: wName=%s, HWND=%d, profile=%s', self.i, wName, hwnd, self._wProfile)
        
        return {
            'hwnd': hwnd,
            'wName': wName,
            'sleepTime': 1,
            # 設定值
            'teamPosition': self.readIntFromConfig('Common', 'TeamPosition'),
            'hpCure': self.readIntFromConfig('Thresholds', 'HpCure'),
            'mpTransHP': self.readIntFromConfig('Thresholds', 'MpTransHP'),
            'mpProtect': self.readIntFromConfig('Thresholds', 'MpProtect'),
            'hpBackHome': self.readIntFromConfig('Thresholds', 'HpBackHome'),
            'role': self.readStrFromConfig('Common', 'Role'),
            'backHomeKey': self.readStrFromConfig('Hotkey', 'BackHomeKey'),
            'teleportKey': self.readStrFromConfig('Hotkey', 'TeleportKey'),
            'cureKey': self.readStrFromConfig('Hotkey', 'CureKey'),
            'transHpKey': self.readStrFromConfig('Hotkey', 'TransHpKey'),
            'majorAttackKey': self.readStrFromConfig('Hotkey', 'MajorAttackKey'),
            'minorAttackKey': self.readStrFromConfig('Hotkey', 'MinorAttackKey'),
            # 時間追蹤
            'lastHomeTeleport': datetime.now(),
            'lastRndTeleport': datetime.now(),
            'lastNotAttacked': datetime.now(),
            # 計數器
            'notAttackCnt': 0,
            'notAttackAlertTimes': 30,
            'darkCnt': 0,
        }

    def _tick(self, ctx):
        """單次迴圈迭代"""
        now = datetime.now()
        hwnd = ctx['hwnd']
        wName = ctx['wName']
        
        # Phase 1: 世界王檢查
        self._check_boss(ctx, now)
        
        # Phase 2: 視窗顯示/隱藏
        self._handle_window_visibility(hwnd)
        
        # Phase 3: 截圖
        self.img = getWindow_Img(hwnd)
        if self.img is None:
            return
        
        # Phase 4: 偵測畫面狀態
        state = self._detect_state(ctx)
        
        # Phase 5: 決定動作
        action_info, new_sleep = self._decide_action(ctx, state, now)
        ctx['sleepTime'] = new_sleep
        
        # Phase 6: 輸出結果
        endTime = datetime.now()
        executeTime = (endTime - now).microseconds / 1000
        
        hp = state.get('hp', -1)
        mp = state.get('mp', -1)
        fullInfo = 'HP:%03d，MP:%03d，共執行%d毫秒，' % (hp, mp, executeTime) + action_info
        
        # 更新截圖到 GUI
        if self.i == self.tkObj.showIndex:
            self._update_image(self.img)
        
        self._update_status(fullInfo)

    def _check_boss(self, ctx, now):
        """檢查世界王時段"""
        runBoss, weekDay, idx = self.isRunBoss()
        if runBoss:
            self.bossQuestRun(ctx['hwnd'], ctx['wName'], ctx['backHomeKey'], weekDay, idx)
            ctx['lastHomeTeleport'] = now + timedelta(minutes=10)

    def _handle_window_visibility(self, hwnd):
        """處理視窗顯示/隱藏"""
        x, y, width, height = getWindow_W_H(hwnd)
        isHide = self._should_hide_window()
        if isHide and x <= 8000 and y <= 8000:
            setWindowPosition(hwnd, x + 10000, y + 10000, width, height)
        elif not isHide and x >= 8000 and y >= 8000:
            setWindowPosition(hwnd, x - 10000, y - 10000, width, height)

    def _detect_state(self, ctx):
        """偵測當前畫面狀態，回傳 state dict"""
        state = {
            'hp': -1,
            'mp': -1,
            'isPosion': False,
            'isTeamEnabled': False,
            'isGrey': 0,
            'isRightPanelOpened': False,
            'isAttack': False,
            'isAttacked': False,
        }
        
        state['isTeamEnabled'], state['isGrey'] = detectTeamEnabled(self.img)
        state['isRightPanelOpened'] = detectItemSkillPanelOpened(self.img)
        state['isAttacked'] = detectIsAttacked(self.img)
        
        teamPosition = ctx['teamPosition']
        
        if state['isTeamEnabled'] and not state['isRightPanelOpened']:
            if detectTeamPositionAvalible(self.img, teamPosition):
                state['hp'], state['isPosion'] = detectHPPercent(self.img, teamPosition, 255)
                state['mp'] = detectMPPercent(self.img, teamPosition, 255)
            elif detectTeamPositionAvalible(self.img, 0):
                state['hp'], state['isPosion'] = detectHPPercent(self.img, 0, 255)
                state['mp'] = detectMPPercent(self.img, 0, 255)
            
            state['isAttack'] = detectIsAttack(self.img)
        
        return state

    def _decide_action(self, ctx, state, now):
        """根據狀態決定動作，回傳 (infoText, sleepTime)"""
        hwnd = ctx['hwnd']
        wName = ctx['wName']
        info = ""
        sleepTime = 1  # 預設
        
        # === 被攻擊處理 ===
        if state['isAttacked'] and (now - ctx['lastHomeTeleport']).seconds > 3:
            self.pressKey(hwnd, wName, ctx['teleportKey'])
            info += "被打囉。"
            self.logToConsole(info)
            ctx['lastRndTeleport'] = now
        else:
            ctx['lastNotAttacked'] = now
        
        # === 無法偵測狀態 ===
        if not (state['isTeamEnabled'] and not state['isRightPanelOpened']):
            if not state['isTeamEnabled']:
                info = "無法偵測組隊狀態"
            if state['isRightPanelOpened']:
                info = "道具或技能欄打開"
            info += "暫不動作。"
            ctx['notAttackCnt'] += 1
            return info, 2
        
        # === 戰鬥邏輯 ===
        info += "戰鬥狀態:%r," % state['isAttack']
        hp = state['hp']
        mp = state['mp']
        
        # 回捲判斷
        if hp < ctx['hpBackHome'] and hp > 0 and (now - ctx['lastHomeTeleport']).seconds >= 5:
            return self._action_back_home(ctx, state, now, info)
        
        # 解毒
        if state['isPosion']:
            self.pressKey(hwnd, wName, ctx['cureKey'])
            info += "解毒。"
            return info, sleepTime
        
        # 治癒（非騎士）
        if hp < ctx['hpCure'] and hp > 0 and ctx['role'] != 'KNIGHT':
            if mp > 5:
                self.pressKey(hwnd, wName, ctx['cureKey'])
                info += "施放治癒魔法。"
                return info, 0
        
        # 攻擊魔法
        if mp >= ctx['mpProtect'] and state['isAttack']:
            self.pressKey(hwnd, wName, ctx['majorAttackKey'])
            info += "施放攻擊魔法。"
            return info, 0.4
        
        # 妖精非戰鬥時魂體轉換
        if not state['isAttack'] and mp < 90 and ctx['role'] == 'ELF' and mp >= 0:
            self.pressKey(hwnd, wName, ctx['transHpKey'])
            info += "MP<90%，施放魂體轉換。"
            return info, 1.4
        
        # MP 不足時魂體轉換
        if mp < ctx['mpProtect'] and mp < 90 and hp >= ctx['mpTransHP']:
            self.pressKey(hwnd, wName, ctx['transHpKey'])
            info += "施放魂體轉換。"
            return info, 1.4
        
        # 什麼都不做
        info += "啥也不做。"
        return info, 0.5

    def _action_back_home(self, ctx, state, now, info):
        """執行回捲動作"""
        hwnd = ctx['hwnd']
        wName = ctx['wName']
        
        self.pressKey(hwnd, wName, ctx['backHomeKey'])
        info += "點擊回捲。"
        
        if state['isAttacked']:
            for bh in range(4):
                self.pressKey(hwnd, wName, ctx['backHomeKey'])
                self.logToConsole("backHome - PVP %r" % bh)
                sleep(0.5)
        else:
            self.logToConsole("backHome")
        
        self.logToConsole(info)
        ctx['lastHomeTeleport'] = now
        self.doBeep(5)
        
        return info, 1

    # ====== 工具方法 ======

    def pvpBackHome(self, hwnd, wName, backHomeKey, isAttacked, execTimes):
        if isAttacked:
            for bh in range(execTimes):
                self.pressKey(hwnd, wName, backHomeKey)
                self.logToConsole("backHome - PVP %r" % bh)
                sleep(0.5)

    # 必要的 profile key——缺少時用預設值
    REQUIRED_KEYS = {
        'Common': ['TeamPosition', 'Role'],
        'Thresholds': ['HpCure', 'MpTransHP', 'MpProtect', 'HpBackHome'],
        'Hotkey': ['BackHomeKey'],
    }

    def loadProfile(self, configFile: str) -> None:
        profile_path = 'profile/' + configFile
        if not self.profileConfig.read(profile_path):
            log.error('Thread-%d: 無法讀取 profile: %s', self.i, profile_path)
            return
        
        # 驗證必要的 key
        for section, keys in self.REQUIRED_KEYS.items():
            if not self.profileConfig.has_section(section):
                log.warning('Thread-%d: profile 缺少 section [%s]', self.i, section)
                continue
            for key in keys:
                if not self.profileConfig.has_option(section, key):
                    log.warning('Thread-%d: profile 缺少 [%s]%s，將使用預設值', self.i, section, key)

    def readFromConfig(self, sector: str, key: str, default: str = '') -> str:
        try:
            return self.profileConfig[sector][key]
        except (KeyError, ValueError) as e:
            log.warning('設定讀取失敗 [%s]%s: %s，使用預設值: %s', sector, key, e, default)
            return default

    def readStrFromConfig(self, sector: str, key: str, default: str = '') -> str:
        return str(self.readFromConfig(sector, key, default))

    def readIntFromConfig(self, sector: str, key: str, default: int = 0) -> int:
        try:
            return int(self.readFromConfig(sector, key, str(default)))
        except (ValueError, TypeError):
            log.warning('設定值轉換 int 失敗 [%s]%s，使用預設值: %d', sector, key, default)
            return default

    def saveImage(self, img, wName, imgType):
        if not path.exists("LinMOut"):
            mkdir("LinMOut")
        nowStr = strftime('%Y%m%d-%H-%M-%S.png')
        imgName = 'LinMOut/' + wName + "_" + imgType + '_' + nowStr
        img.save(imgName, "PNG")

    def pressKey(self, hwnd, wName, key):
        self.adb_tap(wName, key)

    def adb_tap(self, wName, pos):
        keyDict = {
            '1': LinMKeySet.key1, '2': LinMKeySet.key2,
            '3': LinMKeySet.key3, '4': LinMKeySet.key4,
            '5': LinMKeySet.key5, '6': LinMKeySet.key6,
            '7': LinMKeySet.key7, '8': LinMKeySet.key8,
            '9': LinMKeySet.key9, '0': LinMKeySet.key0,
        }

        if not isinstance(pos, LinMKeySet) and pos in keyDict:
            pos = keyDict[pos]

        if isinstance(pos, LinMKeySet) and pos is not None:
            # 使用 emulator_config 的解析度做座標縮放
            x, y = scale_pos(pos, emulator_config.base_width, emulator_config.base_height)
            execCmd = emulator_config.build_adb_tap_cmd(wName, x, y)
            try:
                result = subprocess.run(execCmd, shell=True, capture_output=True, text=True, timeout=10)
                rst = result.stdout.strip()
                if rst and rst[0:5] == 'error':
                    log.error('ADB error: %s', rst)
                    ipAddr = rst.split("'")[1]
                    log.info('嘗試重新連線: %s', ipAddr)
                    reconnectCmd = emulator_config.build_adb_connect_cmd(ipAddr)
                    reconnResult = subprocess.run(reconnectCmd, shell=True, capture_output=True, text=True, timeout=10)
                    log.info('重連結果: %s', reconnResult.stdout.strip())
            except subprocess.TimeoutExpired:
                log.warning('adb_tap 逾時: %s', wName)
            except Exception as e:
                log.error('adb_tap 錯誤: %s', e)
        else:
            log.warning('adb_tap 無效按鍵: %s', pos)
    
    def doBeep(self, cnt):
        t = Thread(target=self.beep, args=(cnt,))
        t.start()
    
    def beep(self, cnt):
        for i in range(cnt):
            Beep(1500, 100)
            sleep(0.4)

    def logToConsole(self, msg: str) -> None:
        log.info(msg)
        
    def bossQuestRun(self, hwnd, wName: str, backHomeKey, weekDay: int, idx: int) -> None:
        log.info('進入副本腳本，先按回捲') 
        self.pressKey(hwnd, wName, backHomeKey)        
        log.info('避免村莊lag，等個 10sec + 亂數')
        sleep(10 + random.randint(0, 10))
        
        if weekDay in [4] and idx in [5]:
            self.pressKey(hwnd, wName, LinMKeySet.bossQuest2)        
        else:
            self.pressKey(hwnd, wName, LinMKeySet.bossQuest)
        sleep(3)
        log.info('點擊確認')
        self.pressKey(hwnd, wName, LinMKeySet.key2)
        
        log.info('等待世界王開始')
        while self._is_running():
            sleep(10)
            min_val = int(datetime.now().strftime('%M'))
            if min_val == 0:
                self.pressKey(hwnd, wName, LinMKeySet.autoBtn)
                break
        
        if not self._is_running():
            log.info('等待世界王期間被停止')
            return
            
        log.info('開始打王！結束腳本')

    def isRunBoss(self) -> Tuple[bool, Optional[int], Optional[int]]:
        now = datetime.now()
        m = int(now.strftime('%M'))
        s = int(now.strftime('%S'))
        weekDay = now.weekday()
        runBoss = 0
        idx = None
        
        if m == (60 - self.beforeMinutes) and 5 <= s <= 10:
            nextBossTimeStr = (now + timedelta(minutes=self.beforeMinutes)).strftime('%H:%M')           
            try:
                idx = self.tkObj.bossTimeList.index(nextBossTimeStr)
                runBoss = self.tkObj.bossTimeVariable[idx].get()
                
                if idx in [2, 3] and weekDay == 6:
                    runBoss = 0
            except Exception:
                runBoss = 0
        
        if runBoss == 0:
            return False, None, None
        else:
            return True, weekDay, idx
