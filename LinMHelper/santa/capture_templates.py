"""
模板擷取工具 — 從遊戲截圖中框選並儲存模板圖片。

使用方式:
    python -m santa.capture_templates --live <window_name>   從遊戲視窗擷取
    python -m santa.capture_templates <screenshot.png>        從截圖檔擷取
    python -m santa.capture_templates --review                僅檢視/管理已存模板
"""
import sys
import os
import cv2
import numpy as np
import numpy as np
from PIL import Image
from santa.roi_config import ROI

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')

TEMPLATES = [
    {
        'name': 'team_enabled',
        'title': '組隊狀態 UI',
        'desc': '請框選「組隊列表」左側的白色直條區域。\n'
                '這是畫面左側顯示隊伍成員血條的那一整塊 UI。\n'
                '確保組隊 UI 有顯示時再擷取。',
        'hint_x': ROI.Team.cp1_x, 'hint_y': ROI.Team.cp1_y1, 
        'hint_w': ROI.Team.cp2_x - ROI.Team.cp1_x, 
        'hint_h': ROI.Team.cp1_y2 - ROI.Team.cp1_y1,
        'color': (0, 255, 0),
    },
    {
        'name': 'panel_opened',
        'title': '道具/技能面板',
        'desc': '請框選右側「道具」或「技能」面板展開時的特徵區域。\n'
                '先打開道具或技能面板再擷取。\n'
                '建議擷取面板邊框或標題列的一小塊。',
        'hint_x': ROI.Panel.x, 'hint_y': ROI.Panel.y1, 
        'hint_w': 20, 'hint_h': ROI.Panel.y2 - ROI.Panel.y1,
        'color': (255, 165, 0),
    },
    {
        'name': 'is_attack',
        'title': '攻擊狀態指示',
        'desc': '請框選角色「正在攻擊」時才會出現的 UI 元素。\n'
                '通常在畫面右下方，戰鬥時會出現紅色劍/攻擊圖示。\n'
                '確保角色正在戰鬥中再擷取。',
        'hint_x': ROI.Attack.x1, 'hint_y': ROI.Attack.y, 
        'hint_w': ROI.Attack.x2 - ROI.Attack.x1, 'hint_h': 5,
        'color': (0, 0, 255),
    },
    {
        'name': 'is_attacked',
        'title': '被攻擊指示',
        'desc': '請框選角色「被其他玩家攻擊」時才會出現的特徵。\n'
                '通常畫面邊緣會閃紅光或出現 PK 標記。\n'
                '如果無法重現此情況，可按 ESC 跳過（使用像素偵測）。',
        'hint_x': ROI.Attacked.area1_x1, 'hint_y': ROI.Attacked.area1_y0, 
        'hint_w': ROI.Attacked.area1_x2 - ROI.Attacked.area1_x1,
        'hint_h': ROI.Attacked.area1_y_range,
        'color': (128, 0, 255),
    },
]

# 縮圖最大尺寸
THUMB_MAX_W = 250
THUMB_MAX_H = 150


def _load_template_thumb(name):
    """載入模板並縮放為縮圖"""
    path = os.path.join(TEMPLATE_DIR, f'{name}.png')
    if not os.path.exists(path):
        return None, None
    img = cv2.imread(path)
    if img is None:
        return None, None
    
    orig_h, orig_w = img.shape[:2]
    scale = min(THUMB_MAX_W / orig_w, THUMB_MAX_H / orig_h, 1.0)
    new_w = int(orig_w * scale)
    new_h = int(orig_h * scale)
    thumb = cv2.resize(img, (new_w, new_h))
    return thumb, (orig_w, orig_h)


def _build_review_image(selected_idx=0):
    """建立模板預覽總覽圖"""
    cols = 2
    rows = 2
    cell_w = THUMB_MAX_W + 40
    cell_h = THUMB_MAX_H + 80
    canvas_w = cell_w * cols + 20
    canvas_h = cell_h * rows + 100  # 底部留空給操作提示
    
    canvas = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint8)
    canvas[:] = (50, 50, 50)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    # 標題
    cv2.putText(canvas, "Template Review", (15, 30), font, 0.8, (255, 255, 255), 2)
    
    for i, tmpl in enumerate(TEMPLATES):
        row = i // cols
        col = i % cols
        x0 = col * cell_w + 20
        y0 = row * cell_h + 50
        
        # 選中框
        border_color = (0, 200, 255) if i == selected_idx else (100, 100, 100)
        cv2.rectangle(canvas, (x0 - 5, y0 - 5), (x0 + cell_w - 35, y0 + cell_h - 25), border_color, 2)
        
        # 序號 + 名稱
        status_icon = ""
        thumb, orig_size = _load_template_thumb(tmpl['name'])
        if thumb is not None:
            status_icon = "[OK]"
            status_color = (0, 255, 0)
        else:
            status_icon = "[NONE]"
            status_color = (0, 0, 255)
        
        label = f"{i+1}. {tmpl['name']}"
        cv2.putText(canvas, label, (x0 + 2, y0 + 15), font, 0.45, (255, 255, 255), 1)
        cv2.putText(canvas, status_icon, (x0 + 2, y0 + 33), font, 0.4, status_color, 1)
        
        # 縮圖
        thumb_y = y0 + 42
        if thumb is not None:
            th, tw = thumb.shape[:2]
            # 尺寸標註
            size_text = f"{orig_size[0]}x{orig_size[1]}"
            cv2.putText(canvas, size_text, (x0 + 2 + tw + 5, thumb_y + th // 2), font, 0.35, (180, 180, 180), 1)
            # 貼上縮圖
            canvas[thumb_y:thumb_y+th, x0+2:x0+2+tw] = thumb
        else:
            # 無模板的灰色佔位
            cv2.rectangle(canvas, (x0 + 2, thumb_y), (x0 + THUMB_MAX_W, thumb_y + 60), (80, 80, 80), -1)
            cv2.putText(canvas, "No template", (x0 + 50, thumb_y + 35), font, 0.5, (150, 150, 150), 1)
            cv2.putText(canvas, "(pixel fallback)", (x0 + 45, thumb_y + 55), font, 0.35, (120, 120, 120), 1)
    
    # 底部操作提示
    tip_y = canvas_h - 50
    cv2.putText(canvas, "Keys:  1-4=select  D=delete  R=re-capture  F=full view  S=save  ESC=done",
                (15, tip_y), font, 0.38, (200, 255, 200), 1)
    cv2.putText(canvas, "Selected template is highlighted in YELLOW border.",
                (15, tip_y + 22), font, 0.38, (180, 180, 180), 1)
    
    return canvas


def _draw_roi_overlay(full_img):
    """在完整截圖上疊加各模板的比對結果和 ROI 位置"""
    annotated = full_img.copy()
    font = cv2.FONT_HERSHEY_SIMPLEX
    
    for tmpl in TEMPLATES:
        name = tmpl['name']
        tmpl_path = os.path.join(TEMPLATE_DIR, f'{name}.png')
        if not os.path.exists(tmpl_path):
            continue
        
        template = cv2.imread(tmpl_path)
        if template is None:
            continue
        
        # 灰階比對
        gray_img = cv2.cvtColor(annotated, cv2.COLOR_BGR2GRAY)
        gray_tmpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        try:
            result = cv2.matchTemplate(gray_img, gray_tmpl, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, max_loc = cv2.minMaxLoc(result)
        except Exception:
            continue
        
        th, tw = gray_tmpl.shape[:2]
        color = tmpl['color']
        
        # 畫框
        pt1 = max_loc
        pt2 = (max_loc[0] + tw, max_loc[1] + th)
        cv2.rectangle(annotated, pt1, pt2, color, 2)
        
        # 標籤
        conf_text = f'{name} ({max_val:.2f})'
        label_y = max(pt1[1] - 8, 15)
        cv2.putText(annotated, conf_text, (pt1[0], label_y), font, 0.45, color, 1)
    
    # 底部提示
    h = annotated.shape[0]
    cv2.putText(annotated, 'Press any key to close', (10, h - 10), font, 0.5, (200, 200, 200), 1)
    
    return annotated


def _capture_live_screenshot(live_wName):
    """從遊戲視窗即時截取一張截圖，回傳 cv2 格式"""
    from santa.Lib32 import FindWindow_bySearch, getWindow_Img
    
    hwnd = FindWindow_bySearch(live_wName)
    if hwnd is None:
        print(f'  ⚠️  找不到視窗: {live_wName}')
        return None
    
    print(f'  📸 正在從 [{live_wName}] 截取畫面...')
    pil_img = getWindow_Img(hwnd)
    if pil_img is None:
        print('  ⚠️  截圖失敗')
        return None
    
    # PIL → cv2
    rgb = np.array(pil_img)
    if rgb.shape[2] == 4:
        rgb = rgb[:, :, :3]
    cv2_img = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    
    # 保存完整截圖
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    full_path = os.path.join(TEMPLATE_DIR, '_full_screenshot.png')
    cv2.imwrite(full_path, cv2_img)
    print(f'  ✅ 截圖完成 ({cv2_img.shape[1]}x{cv2_img.shape[0]})，已存: {full_path}')
    return cv2_img


def review_templates(source_img=None, live_wName=None):
    """
    模板預覽管理介面。
    按 1-4 選擇模板 → D 刪除 / R 重新擷取。
    若有設定 live_wName，按 R 時會自動從遊戲視窗截取最新畫面。
    """
    selected = 0
    window_name = "Template Manager"
    
    has_source = source_img is not None or live_wName is not None
    recapture_hint = '自動從遊戲截取' if live_wName else '需要有截圖來源'
    
    print()
    print('=' * 60)
    print('  模板管理介面')
    print('=' * 60)
    print('  按 1~4 選擇模板')
    print('  按 D   刪除選取的模板')
    print(f'  按 R   重新擷取選取的模板（{recapture_hint}）')
    print('  按 F   查看完整截圖 + ROI 標示')
    print('  按 S   儲存當前遊戲截圖')
    print('  按 ESC 或 Q 離開')
    print('=' * 60)
    
    while True:
        canvas = _build_review_image(selected)
        cv2.imshow(window_name, canvas)
        key = cv2.waitKey(0) & 0xFF
        
        # 1-4 選擇
        if ord('1') <= key <= ord('4'):
            selected = key - ord('1')
        
        # D = 刪除
        elif key == ord('d') or key == ord('D'):
            tmpl = TEMPLATES[selected]
            path = os.path.join(TEMPLATE_DIR, f'{tmpl["name"]}.png')
            if os.path.exists(path):
                os.remove(path)
                print(f'  🗑️  已刪除: {tmpl["name"]}')
            else:
                print(f'  ⚠️  {tmpl["name"]} 不存在，無需刪除')
        
        # R = 重新擷取
        elif key == ord('r') or key == ord('R'):
            # 決定截圖來源
            current_src = source_img
            if current_src is None and live_wName:
                current_src = _capture_live_screenshot(live_wName)
            
            if current_src is None:
                print('  ⚠️  沒有截圖來源，無法重新擷取')
                print('     請用 --review --live <window_name>')
                continue
            
            tmpl = TEMPLATES[selected]
            cv2.destroyWindow(window_name)
            
            print(f'\n  重新擷取: {tmpl["title"]} ({tmpl["name"]})')
            print(f'  {tmpl["desc"]}')
            
            guide = draw_guide(current_src, tmpl, selected + 1, len(TEMPLATES))
            roi_window = f'Re-capture: {tmpl["name"]}'
            roi = cv2.selectROI(roi_window, guide, fromCenter=False, showCrosshair=True)
            cv2.destroyWindow(roi_window)
            
            x, y, w, h = roi
            if w > 0 and h > 0:
                template = current_src[y:y+h, x:x+w]
                save_path = os.path.join(TEMPLATE_DIR, f'{tmpl["name"]}.png')
                cv2.imwrite(save_path, template)
                print(f'  ✅ 已重新儲存: {save_path} ({w}x{h})')
            else:
                print(f'  ⏭️  已取消')
        
        # F = 查看完整截圖 + ROI 標示
        elif key == ord('f') or key == ord('F'):
            full_path = os.path.join(TEMPLATE_DIR, '_full_screenshot.png')
            if os.path.exists(full_path):
                full_img = cv2.imread(full_path)
                annotated = _draw_roi_overlay(full_img)
                cv2.imshow('Full Screenshot + ROI', annotated)
                print('  📷 顯示完整截圖（按任意鍵關閉）')
                cv2.waitKey(0)
                cv2.destroyWindow('Full Screenshot + ROI')
            else:
                print('  ⚠️  尚無完整截圖，請先按 S 儲存或用 R 重新擷取')
        
        # S = 即時儲存遊戲截圖
        elif key == ord('s') or key == ord('S'):
            if live_wName:
                _capture_live_screenshot(live_wName)
                print('  💾 截圖已儲存至 templates/_full_screenshot.png')
            else:
                print('  ⚠️  未指定遊戲視窗，無法截圖')
                print('     請用 --review --live <window_name>')
        
        # ESC or Q = 離開
        elif key == 27 or key == ord('q') or key == ord('Q'):
            break
    
    cv2.destroyAllWindows()
    print('\n  已離開模板管理介面。')


def draw_guide(img, template_info, step, total):
    """在截圖上畫出指引資訊"""
    guide = img.copy()
    h, w = guide.shape[:2]
    
    overlay = guide.copy()
    cv2.rectangle(overlay, (0, 0), (w, 130), (40, 40, 40), -1)
    cv2.addWeighted(overlay, 0.85, guide, 0.15, 0, guide)
    
    font = cv2.FONT_HERSHEY_SIMPLEX
    title = f"[{step}/{total}] Template: {template_info['name']}"
    cv2.putText(guide, title, (15, 30), font, 0.8, (255, 255, 255), 2)
    cv2.putText(guide, "Drag mouse to select ROI -> Enter/Space to confirm", 
                (15, 60), font, 0.55, (200, 255, 200), 1)
    cv2.putText(guide, "Press C to re-select | Press ESC to skip",
                (15, 85), font, 0.55, (200, 200, 255), 1)
    
    hint = template_info
    hx = int(hint['hint_x'] * w / 100)
    hy = int(hint['hint_y'] * h / 100)
    hw = int(hint['hint_w'] * w / 100)
    hh = int(hint['hint_h'] * h / 100)
    color = hint['color']
    
    dash_len = 10
    for i in range(0, hw, dash_len * 2):
        cv2.line(guide, (hx + i, hy), (hx + min(i + dash_len, hw), hy), color, 2)
        cv2.line(guide, (hx + i, hy + hh), (hx + min(i + dash_len, hw), hy + hh), color, 2)
    for i in range(0, hh, dash_len * 2):
        cv2.line(guide, (hx, hy + i), (hx, hy + min(i + dash_len, hh)), color, 2)
        cv2.line(guide, (hx + hw, hy + i), (hx + hw, hy + min(i + dash_len, hh)), color, 2)
    
    label = f"<-- Suggested area for [{template_info['name']}]"
    cv2.putText(guide, label, (hx + hw + 8, hy + hh // 2 + 5), font, 0.5, color, 1)
    cv2.putText(guide, "The dashed box shows the SUGGESTED area. You can select any region.",
                (15, h - 15), font, 0.45, (180, 180, 180), 1)
    
    return guide


def capture_from_image(img_path):
    """從截圖中互動式框選並儲存模板"""
    img = cv2.imread(img_path)
    if img is None:
        print(f'無法載入圖片: {img_path}')
        return
    
    os.makedirs(TEMPLATE_DIR, exist_ok=True)
    total = len(TEMPLATES)
    
    print('=' * 60)
    print('  模板擷取工具')
    print('=' * 60)
    
    for i, tmpl in enumerate(TEMPLATES):
        name = tmpl['name']
        existing = os.path.join(TEMPLATE_DIR, f'{name}.png')
        status = '⚠ 已存在，會覆蓋' if os.path.exists(existing) else '尚未建立'
        
        print(f'\n{"─" * 60}')
        print(f'  [{i+1}/{total}] {tmpl["title"]} ({name})')
        print(f'  狀態: {status}')
        print(f'{"─" * 60}')
        print(f'  {tmpl["desc"]}')
        print()
        print(f'  👉 在彈出的視窗中用滑鼠框選區域')
        print(f'     虛線框 = 建議框選位置（僅供參考）')
        print(f'     Enter/Space = 確認  |  C = 重選  |  ESC = 跳過')
        
        guide_img = draw_guide(img, tmpl, i + 1, total)
        window_name = f'[{i+1}/{total}] {tmpl["title"]} ({name})'
        roi = cv2.selectROI(window_name, guide_img, fromCenter=False, showCrosshair=True)
        cv2.destroyAllWindows()
        
        x, y, w, h = roi
        if w > 0 and h > 0:
            template = img[y:y+h, x:x+w]
            save_path = os.path.join(TEMPLATE_DIR, f'{name}.png')
            cv2.imwrite(save_path, template)
            print(f'  ✅ 已儲存: {save_path} ({w}x{h})')
        else:
            print(f'  ⏭️  已跳過')
    
    # 擷取完成後自動進入預覽管理
    print(f'\n{"=" * 60}')
    print('  擷取完成，進入模板預覽管理...')
    print(f'{"=" * 60}')
    review_templates(source_img=img)


def capture_from_live(wName):
    """從即時遊戲視窗截圖中擷取模板"""
    from santa.Lib32 import FindWindow_bySearch, getWindow_Img
    
    hwnd = FindWindow_bySearch(wName)
    if hwnd is None:
        print(f'找不到視窗: {wName}')
        return
    
    print(f'正在截取視窗 [{wName}] ...')
    img = getWindow_Img(hwnd)
    if img is None:
        print('截圖失敗')
        return
    
    tmp_path = os.path.join(TEMPLATE_DIR, '_temp_capture.png')
    img.save(tmp_path, 'PNG')
    print(f'截圖完成 ({img.width}x{img.height})')
    
    capture_from_image(tmp_path)
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('使用方式:')
        print('  從遊戲視窗擷取: python -m santa.capture_templates --live <window_name>')
        print('  從截圖擷取:     python -m santa.capture_templates <screenshot.png>')
        print('  檢視/管理模板:  python -m santa.capture_templates --review')
        print()
        print('會依序要求你框選以下模板:')
        for t in TEMPLATES:
            print(f'  • {t["name"]:20s} — {t["title"]}')
        sys.exit(1)
    
    if sys.argv[1] == '--live':
        if len(sys.argv) < 3:
            print('請指定視窗名稱，例如: python -m santa.capture_templates --live wsh9')
            sys.exit(1)
        capture_from_live(sys.argv[2])
    elif sys.argv[1] == '--review':
        # 支援 --review --live wsh9
        live_name = None
        if len(sys.argv) >= 4 and sys.argv[2] == '--live':
            live_name = sys.argv[3]
        review_templates(live_wName=live_name)
    else:
        capture_from_image(sys.argv[1])
