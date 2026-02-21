"""
統一日誌模組 — 取代散落各處的 print()。
支援同時輸出到 console 和檔案，可配置日誌等級。

使用方式:
    from santa.logger import log
    log.info('一般訊息')
    log.warning('警告')
    log.error('錯誤')
    log.debug('偵錯用')
"""
import logging
import os
import sys
from datetime import datetime


def setup_logger(
    name: str = 'LinMHelper',
    log_dir: str = 'logs',
    console_level: int = logging.INFO,
    file_level: int = logging.DEBUG,
) -> logging.Logger:
    """建立並設定 logger"""
    logger = logging.getLogger(name)
    
    # 避免重複設定
    if logger.handlers:
        return logger
    
    logger.setLevel(logging.DEBUG)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(console_level)
    console_fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)-5s %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)
    
    # File handler（按日期分檔）
    try:
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'{name}_{today}.log')
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(file_level)
        file_fmt = logging.Formatter(
            '[%(asctime)s] %(levelname)-5s [%(threadName)s] %(message)s',
            datefmt='%Y/%m/%d %H:%M:%S'
        )
        file_handler.setFormatter(file_fmt)
        logger.addHandler(file_handler)
    except Exception as e:
        logger.warning(f'無法建立日誌檔: {e}')
    
    return logger


# 全域 logger 單例
log = setup_logger()
