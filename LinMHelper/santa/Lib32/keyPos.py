from enum import Enum

# 基礎解析度（所有座標都在此解析度下定義）
BASE_WIDTH = 1280
BASE_HEIGHT = 720


class LinMKeySet(Enum):
    """按鈕座標，所有 x, y 值皆在 1280x720 mode 下取得"""
    
    # 左上角的按鈕
    characterKey = [45, 30]

    # 底下 4+1+4 按鈕
    key1 = [480, 635]
    key2 = [560, 635]
    key3 = [635, 635]
    key4 = [710, 635]
    key5 = [780, 635]
    questSkill = [860, 635]  # 副本技能按鈕位置
    key6 = [930, 635]
    key7 = [1000, 635]
    key8 = [1075, 635]
    key9 = [1150, 635]
    key0 = [1225, 635]

    # 右上方選單鍵
    bossQuest = [850, 40]
    bossQuest2 = [780, 40]  # 底比斯圖示出現時，世界王按鈕的位置
    upperShop = [930, 40]
    upperitem = [1010, 40]
    upperSkill = [1080, 40]
    upperQuest = [1160, 40]
    upperMain = [1240, 45]

    questBtn = [930, 185]
    questTab1 = [80, 210]
    questTab2 = [80, 290]
    questTab3 = [80, 360]

    # 任務/副本 1 ~ 6
    questBtn1 = [295, 330]
    questBtn2 = [465, 330]
    questBtn3 = [645, 330]
    questBtn4 = [825, 330]
    questBtn5 = [1000, 330]
    questBtn6 = [1180, 330]

    # 接收任務對話，按同意
    acceptQuest = [740, 545]

    # 右下角 auto 鍵
    autoBtn = [970, 510]

    # 僅驗證補充任務次數介面
    cancelBtn = [525, 590]


def scale_pos(key_or_pos, target_width=BASE_WIDTH, target_height=BASE_HEIGHT):
    """
    將 LinMKeySet 座標從基礎解析度 (1280x720) 縮放至目標解析度。
    
    Args:
        key_or_pos: LinMKeySet enum 成員 或 [x, y] list
        target_width: 目標寬度 (像素)
        target_height: 目標高度 (像素)
    
    Returns:
        (x, y) tuple，縮放後的座標
    
    Example:
        >>> scale_pos(LinMKeySet.key1, 1920, 1080)
        (720, 952)
        >>> scale_pos([480, 635], 1920, 1080)
        (720, 952)
    """
    if isinstance(key_or_pos, LinMKeySet):
        raw_x, raw_y = key_or_pos.value
    else:
        raw_x, raw_y = key_or_pos
    
    x = int(raw_x * target_width / BASE_WIDTH)
    y = int(raw_y * target_height / BASE_HEIGHT)
    return x, y
