"""
全域設定常數 — 模擬器路徑、基礎解析度等外部化設定。
可從 Main.ini 的 [Emulator] 區段讀取，或使用預設值。
"""
from configparser import ConfigParser
import os

# 預設值
_DEFAULTS = {
    'nox_path': r'D:\Nox\bin',
    'nox_console': 'NoxConsole.exe',
    'nox_adb': 'nox_adb.exe',
    'base_width': '1280',
    'base_height': '720',
}

class EmulatorConfig:
    """模擬器設定，從 Main.ini [Emulator] 區段讀取"""
    
    def __init__(self):
        self.nox_path = _DEFAULTS['nox_path']
        self.nox_console = _DEFAULTS['nox_console']
        self.nox_adb = _DEFAULTS['nox_adb']
        self.base_width = int(_DEFAULTS['base_width'])
        self.base_height = int(_DEFAULTS['base_height'])
    
    def load_from_ini(self, ini_path='Main.ini'):
        """從 ini 檔讀取 [Emulator] 區段，缺少的 key 使用預設值"""
        config = ConfigParser()
        config.read(ini_path)
        
        if 'Emulator' in config:
            section = config['Emulator']
            self.nox_path = section.get('NoxPath', self.nox_path)
            self.nox_console = section.get('NoxConsole', self.nox_console)
            self.nox_adb = section.get('NoxAdb', self.nox_adb)
            self.base_width = int(section.get('BaseWidth', str(self.base_width)))
            self.base_height = int(section.get('BaseHeight', str(self.base_height)))
    
    @property
    def nox_console_path(self):
        """完整的 NoxConsole.exe 路徑"""
        return os.path.join(self.nox_path, self.nox_console)
    
    @property
    def nox_adb_path(self):
        """完整的 nox_adb.exe 路徑"""
        return os.path.join(self.nox_path, self.nox_adb)
    
    def build_adb_tap_cmd(self, wName, x, y):
        """產生 ADB tap 指令"""
        drive = os.path.splitdrive(self.nox_path)[0]
        return (
            f'{drive} & cd "{self.nox_path}" & '
            f'.\\{self.nox_console} adb -name:{wName} '
            f'-command:"shell input tap {x} {y}"'
        )
    
    def build_adb_connect_cmd(self, ipAddr):
        """產生 ADB reconnect 指令"""
        drive = os.path.splitdrive(self.nox_path)[0]
        return (
            f'{drive} & cd "{self.nox_path}" & '
            f'.\\{self.nox_adb} connect {ipAddr}'
        )
    
    def save_defaults_to_ini(self, config):
        """若 ini 檔沒有 [Emulator] 區段，寫入預設值"""
        if 'Emulator' not in config:
            config['Emulator'] = {
                'NoxPath': self.nox_path,
                'NoxConsole': self.nox_console,
                'NoxAdb': self.nox_adb,
                'BaseWidth': str(self.base_width),
                'BaseHeight': str(self.base_height),
            }


# 全域單例
emulator_config = EmulatorConfig()
