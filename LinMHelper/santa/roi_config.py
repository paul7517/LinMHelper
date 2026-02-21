"""
ROI (Region of Interest) 設定 — 集中管理 ImageUtils 裡所有偵測用的座標百分比。
所有值以「畫面百分比」表示（0~100），實際像素由 ImageUtils 在運行時換算。
"""


class ROI:
    """偵測區域座標百分比集中管理"""
    
    # ====== 組隊狀態偵測 (detectTeamEnabled) ======
    class Team:
        # check point 1: 左側直條
        cp1_x = 10.25
        cp1_y1 = 23.88
        cp1_y2 = 25.83
        cp1_rgb_threshold = 200  # (原為220) 放寬顏色判定
        
        # check point 2: 右側直條
        cp2_x = 27.55
        cp2_y1 = 22.80
        cp2_y2 = 25.95
        cp2_min_count = 1  # (原為3) 只要掃到 1 個高亮就算數
    
    # ====== 組隊位置偵測 (detectTeamPositionAvalible) ======
    class TeamPosition:
        x = 17.2
        base_y = 37.7
        y_step = 8.8  # 每個隊員間距
        rgb_sum_min = 700
        rgb_sum_max = 770
    
    # ====== 道具/技能面板偵測 (detectItemSkillPanelOpened) ======
    class Panel:
        x = 71.23
        y1 = 20.88
        y2 = 61.43
        match_threshold_pct = 72.0  # 匹配像素佔比 >= 此值判定為開啟
    
    # ====== 血條偵測 (detectHPPercent) ======
    class HP:
        x1 = 5.7
        x2 = 14.1
        base_y_offset = 2.8 + 35.38  # 基礎 Y 偏移
        y_step = 8.8  # 每個隊員間距
        
        # 血量顏色範圍 (R, G, B)
        hp_r_range = (137, 205)
        hp_g_range = (0, 15)
        hp_b_range = (0, 15)
        
        # 中毒顏色範圍
        poison_r_range = (4, 25)
        poison_g_range = (40, 55)
        poison_b_range = (0, 15)
    
    # ====== 魔力條偵測 (detectMPPercent) ======
    class MP:
        x1 = 5.7
        x2 = 14.1
        base_y_offset = 2.8 + 37.00
        y_step = 8.8
        
        mp_r_range = (0, 21)
        mp_g_range = (60, 125)
        mp_b_range = (110, 202)
    
    # ====== 攻擊狀態偵測 (detectIsAttack) ======
    class Attack:
        x1 = 83.8
        x2 = 87.0
        y = 69.07
        r_minus_g_threshold = 64
        r_minus_b_threshold = 90
        rate_threshold = 17  # attRate >= 此值判定攻擊中
    
    # ====== 被攻擊偵測 (detectIsAttacked) ======
    class Attacked:
        # 區域 1: 右下角
        area1_x1 = 93.0
        area1_x2 = 94.0
        area1_y0 = 75.5
        area1_y_range = 1.5
        area1_r_threshold = 220
        area1_r_minus_g = 64
        area1_rate_threshold = 50
        
        # 區域 2: 左上角
        area2_x1 = 0.5
        area2_x2 = 5.0
        area2_y = 2.0
        area2_r_minus_g = 48
        area2_r_minus_b = 90
        area2_rate_threshold = 2
