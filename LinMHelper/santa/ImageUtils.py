"""
影像偵測工具 — 混合式偵測策略：
  1. 若 santa/templates/ 下有對應模板 → 使用 cv2.matchTemplate（更穩健）
  2. 否則 fallback 到像素 RGB 掃描（原始方式）

所有偵測座標由 roi_config.ROI 集中管理。
"""
from santa.roi_config import ROI
from santa.template_detector import detector


# ====== 組隊狀態 ======

def detectTeamEnabled(img):
    """偵測組隊狀態是否啟用（模板 'team_enabled'）"""
    
    # 嘗試模板比對
    if detector.has_template('team_enabled'):
        matched, conf, loc = detector.match_template(img, 'team_enabled', threshold=0.65)
        return matched, 0
    
    # fallback: 像素偵測
    roi = ROI.Team
    intX = int(roi.cp1_x * img.width / 100)
    intY1 = int(roi.cp1_y1 * img.height / 100)
    intY2 = int(roi.cp1_y2 * img.height / 100)
    
    cnt = 0
    total = intY2 - intY1
    th = int(total / 3)  # 原本是 /2，改為 1/3 就過關
    for intY in range(intY1, intY2):
        rgb = getPixel(img, intX, intY, 255)
        if rgb[0] > roi.cp1_rgb_threshold and rgb[1] > roi.cp1_rgb_threshold and rgb[2] > roi.cp1_rgb_threshold:
            cnt += 1

    isC1Matched = cnt > th

    intX = int(roi.cp2_x * img.width / 100)
    intY1 = int(roi.cp2_y1 * img.height / 100)
    intY2 = int(roi.cp2_y2 * img.height / 100)

    cnt = 0    
    for intY in range(intY1, intY2):
        rgb = getPixel(img, intX, intY, 255)
        if rgb[0] > roi.cp1_rgb_threshold and rgb[1] > roi.cp1_rgb_threshold and rgb[2] > roi.cp1_rgb_threshold:
            cnt += 1

    isC2Matched = cnt > roi.cp2_min_count
    return isC1Matched and isC2Matched, 0


# ====== 組隊位置 ======

def detectTeamPositionAvalible(img, teamPosition):
    """偵測指定組隊位置是否有效"""
    roi = ROI.TeamPosition
    x = roi.x
    
    position = teamPosition
    if position >= 1:
        position -= 1
    y = roi.base_y + roi.y_step * position
            
    matched = comparePointRGBSum(img, x, y, roi.rgb_sum_min, roi.rgb_sum_max, 0)
    return matched


# ====== 道具/技能面板 ======

def detectItemSkillPanelOpened(img):
    """偵測道具/技能面板是否開啟（模板 'panel_opened'）"""
    
    if detector.has_template('panel_opened'):
        matched, conf, loc = detector.match_template(img, 'panel_opened', threshold=0.75)
        return matched
    
    roi = ROI.Panel
    intX = int(roi.x * img.width / 100)
    intY1 = int(roi.y1 * img.height / 100)
    intY2 = int(roi.y2 * img.height / 100)
    
    cnt = 0
    total = intY2 - intY1
    for intY in range(intY1, intY2):
        if (compareRGB(getPixel(img, intX, intY, -1), (25, 40), (15, 30), (10, 25)) 
           or compareRGB(getPixel(img, intX, intY, -1), (15, 25), (15, 25), (15, 25))):
            cnt += 1
    
    return cnt / total * 100 >= roi.match_threshold_pct


# ====== HP 偵測 ======

def detectHPPercent(img, teamPosition, rgbValue):
    """偵測 HP 百分比及中毒狀態"""
    roi = ROI.HP
    cnt = 0
    status_count = 0
    intX1 = int(roi.x1 * img.width / 100)
    intX2 = int(roi.x2 * img.width / 100)
    
    shiftUnit = 0
    if teamPosition is not None:
        shiftUnit = int(teamPosition)
    if shiftUnit >= 1:
        shiftUnit -= 1

    yPercent = roi.base_y_offset + shiftUnit * roi.y_step
    
    y = int(yPercent * img.height / 100)
    for x in range(intX1, intX2):
        if comparePointRGB(img, x, y, roi.hp_r_range, roi.hp_g_range, roi.hp_b_range, -1):
            cnt += 1
        if comparePointRGB(img, x, y, roi.poison_r_range, roi.poison_g_range, roi.poison_b_range, -1):
            status_count += 1
             
    hpPercent = int(cnt / (intX2 - intX1) * 100)
    return hpPercent, status_count > 0


# ====== MP 偵測 ======

def detectMPPercent(img, teamPosition, rgbValue):
    """偵測 MP 百分比"""
    roi = ROI.MP
    cnt = 0
    intX1 = int(roi.x1 * img.width / 100)
    intX2 = int(roi.x2 * img.width / 100)
    
    shiftUnit = 0
    if teamPosition is not None:
        shiftUnit = int(teamPosition)
    if shiftUnit >= 1:
        shiftUnit -= 1
        
    yPercent = roi.base_y_offset + shiftUnit * roi.y_step
    
    y = int(yPercent * img.height / 100)
    for x in range(intX1, intX2):
        if comparePointRGB(img, x, y, roi.mp_r_range, roi.mp_g_range, roi.mp_b_range, rgbValue):
            cnt += 1
    
    mpPercent = int(cnt / (intX2 - intX1) * 100)
    return mpPercent


# ====== 攻擊狀態 ======

def detectIsAttack(img):
    """偵測是否正在攻擊（模板 'is_attack'）"""
    
    if detector.has_template('is_attack'):
        matched, conf, loc = detector.match_template(img, 'is_attack', threshold=0.7)
        return matched
    
    roi = ROI.Attack
    cnt = 0
    intX1 = int(roi.x1 * img.width / 100)
    intX2 = int(roi.x2 * img.width / 100)

    y = int(roi.y * img.height / 100)    
    for x in range(intX1, intX2):
        rgb = getPixel(img, x, y, 255)
        isAttck = (rgb[0] - rgb[1] > roi.r_minus_g_threshold) or (rgb[0] - rgb[2] > roi.r_minus_b_threshold)
        if isAttck:
            cnt += 1
        y += 1
    
    attRate = cnt / (intX2 - intX1 + 1) * 100 
    return attRate >= roi.rate_threshold


# ====== 被攻擊偵測 ======

def detectIsAttacked(img):
    """偵測是否被攻擊（模板 'is_attacked'）"""
    
    if detector.has_template('is_attacked'):
        matched, conf, loc = detector.match_template(img, 'is_attacked', threshold=0.7)
        return matched
    
    roi = ROI.Attacked
    
    # 區域 1: 右下角
    cnt = 0
    area = 0
    intX1 = int(roi.area1_x1 * img.width / 100)
    intX2 = int(roi.area1_x2 * img.width / 100)
    intY1 = int(roi.area1_y0 * img.height / 100)
    intY2 = int((roi.area1_y0 + roi.area1_y_range) * img.height / 100)
    
    for x in range(intX1, intX2):        
        for y in range(intY1, intY2):
            rgb = getPixel(img, x, y, 255)
            isAttcked = (rgb[0] > roi.area1_r_threshold) and (rgb[0] - rgb[1] > roi.area1_r_minus_g)
            if isAttcked:
                cnt += 1
            area += 1
    
    attRate1 = cnt / area * 100 if area > 0 else 0

    # 區域 2: 左上角
    cnt = 0
    intX1 = int(roi.area2_x1 * img.width / 100)
    intX2 = int(roi.area2_x2 * img.width / 100)
    y = int(roi.area2_y * img.height / 100)
    for x in range(intX1, intX2):        
        rgb = getPixel(img, x, y, 255)
        isAttcked = (rgb[0] - rgb[1] > roi.area2_r_minus_g) or (rgb[0] - rgb[2] > roi.area2_r_minus_b)
        if isAttcked:
            cnt += 1

    attedRate2 = cnt / (intX2 - intX1 + 1) * 100 if (intX2 - intX1 + 1) > 0 else 0

    return (attRate1 > roi.area1_rate_threshold) and (attedRate2 > roi.area2_rate_threshold)


# ====== 底層工具函數 ======

def comparePointRGBSum(img, x, y, rgb_bound1, rgb_bound2, overrideValue):
    """比較單點的 RGB 總和是否在指定範圍"""
    intX, intY = convertIntPosition(img, x, y)
    r, g, b = getPixel(img, intX, intY, overrideValue)
    rgbSum = r + g + b
    return rgbSum >= rgb_bound1 and rgbSum <= rgb_bound2


def comparePointRGB(img, x, y, r_range, g_range, b_range, rgbValue):
    """比對單點的 R, G, B 各自是否在指定範圍"""
    intX, intY = convertIntPosition(img, x, y)
    rgb = getPixel(img, intX, intY, rgbValue)
    rst = compareRGB(rgb, r_range, g_range, b_range)
    
    if rgbValue == -2:
        if not rst:
            print('RGB:%d,%d,%d , Range is %d~%d,%d~%d,%d~%d' % (
                rgb[0], rgb[1], rgb[2],
                r_range[0], r_range[1], g_range[0], g_range[1], b_range[0], b_range[1]))
    return rst


def convertIntPosition(img, fX, fY):
    """座標轉換：百分比 float → 像素 int"""
    if isinstance(fX, float) and isinstance(fY, float):
        intX, intY = int(fX * img.width / 100), int(fY * img.height / 100)
    else:
        intX, intY = fX, fY
    return intX, intY


def getPixel(img, intX, intY, rgbValue):
    """取得 img 裡的 pixel RGB（rgbValue >= 0 時會在圖上標記）"""
    rgb = img.getpixel((intX, intY))
    
    if rgbValue == -2:
        print(rgb)
    
    if rgbValue >= 0:
        img.putpixel((intX, intY), (0, rgbValue, 0))
    return rgb


def compareRGB(rgb, r_range, g_range, b_range):
    """比對 RGB 是否各自在 range 裡"""
    return (rgb[0] >= r_range[0] and rgb[0] <= r_range[1]) and \
           (rgb[1] >= g_range[0] and rgb[1] <= g_range[1]) and \
           (rgb[2] >= b_range[0] and rgb[2] <= b_range[1])


def drawSquares(img, target_point, squares_size):
    """在圖上畫方框標示 ROI"""
    t_x = target_point[0] / 1280.0 * img.width
    t_y = target_point[1] / 720.0 * img.height
    
    for x in range(int(t_x - squares_size), int(t_x + squares_size)):
        for y in range(int(t_y - squares_size), int(t_y + squares_size)):
            getPixel(img, x, y, 255)
    return 0
