"""
模板比對偵測器 — 使用 cv2.matchTemplate 做更穩健的畫面偵測。
當模板圖片存在時使用模板比對，否則 fallback 到像素 RGB 偵測。

使用方式:
    1. 先用 capture_template() 從遊戲截圖中擷取模板
    2. 之後偵測時自動載入模板做比對

模板圖片存放在 santa/templates/ 目錄下。
"""
import os
import cv2
import numpy as np
from PIL import Image

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), 'templates')


class TemplateDetector:
    """模板比對偵測器"""
    
    def __init__(self, template_dir=TEMPLATE_DIR):
        self.template_dir = template_dir
        self._cache = {}  # 模板快取 {name: numpy_array}
        os.makedirs(template_dir, exist_ok=True)
    
    def _get_template_path(self, name):
        """取得模板檔案路徑"""
        return os.path.join(self.template_dir, f'{name}.png')
    
    def has_template(self, name):
        """檢查模板是否存在"""
        return os.path.exists(self._get_template_path(name))
    
    def load_template(self, name):
        """載入模板圖片（含快取）"""
        if name in self._cache:
            return self._cache[name]
        
        path = self._get_template_path(name)
        if not os.path.exists(path):
            return None
        
        template = cv2.imread(path)
        if template is not None:
            self._cache[name] = template
        return template
    
    def clear_cache(self):
        """清除模板快取"""
        self._cache.clear()
    
    def pil_to_cv2(self, pil_img):
        """PIL Image → cv2 numpy array (BGR)"""
        rgb = np.array(pil_img)
        if len(rgb.shape) == 2:
            return rgb  # 灰階
        if rgb.shape[2] == 4:
            rgb = rgb[:, :, :3]  # RGBA → RGB
        return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    
    def cv2_to_pil(self, cv2_img):
        """cv2 numpy array (BGR) → PIL Image"""
        rgb = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB)
        return Image.fromarray(rgb)
    
    # ====== 核心比對方法 ======
    
    def match_template(self, img, template_name, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
        """
        在圖片中搜尋模板，回傳最佳匹配位置和信心度。
        
        Args:
            img: PIL Image 或 cv2 numpy array
            template_name: 模板名稱（不含 .png）
            threshold: 匹配信心度門檻 (0~1)
            method: cv2 匹配方法
        
        Returns:
            (matched, confidence, location) 
            - matched: bool, 是否匹配
            - confidence: float, 最佳匹配信心度
            - location: (x, y, w, h) 或 None
        """
        template = self.load_template(template_name)
        if template is None:
            return False, 0.0, None
        
        if isinstance(img, Image.Image):
            img = self.pil_to_cv2(img)
        
        # 灰階比對（更快、更穩定）
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_tmpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray_img, gray_tmpl, method)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        
        # TM_CCOEFF_NORMED 和 TM_CCORR_NORMED 用 max
        if method in [cv2.TM_SQDIFF, cv2.TM_SQDIFF_NORMED]:
            confidence = 1 - min_val
            loc = min_loc
        else:
            confidence = max_val
            loc = max_loc
        
        h, w = gray_tmpl.shape[:2]
        matched = confidence >= threshold
        location = (loc[0], loc[1], w, h) if matched else None
        
        return matched, confidence, location
    
    def match_template_multi(self, img, template_name, threshold=0.8, method=cv2.TM_CCOEFF_NORMED):
        """
        在圖片中搜尋所有匹配的模板位置。
        
        Returns:
            list of (confidence, x, y, w, h)
        """
        template = self.load_template(template_name)
        if template is None:
            return []
        
        if isinstance(img, Image.Image):
            img = self.pil_to_cv2(img)
        
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray_tmpl = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
        
        result = cv2.matchTemplate(gray_img, gray_tmpl, method)
        h, w = gray_tmpl.shape[:2]
        
        locations = np.where(result >= threshold)
        matches = []
        for pt in zip(*locations[::-1]):  # x, y
            conf = result[pt[1], pt[0]]
            matches.append((float(conf), pt[0], pt[1], w, h))
        
        # NMS: 去重疊（距離太近的只留信心度最高的）
        matches.sort(key=lambda m: m[0], reverse=True)
        filtered = []
        for m in matches:
            too_close = False
            for f in filtered:
                if abs(m[1] - f[1]) < w // 2 and abs(m[2] - f[2]) < h // 2:
                    too_close = True
                    break
            if not too_close:
                filtered.append(m)
        
        return filtered
    
    # ====== 模板擷取工具 ======
    
    def capture_template(self, img, name, x_pct, y_pct, w_pct, h_pct):
        """
        從截圖中擷取指定區域作為模板並儲存。
        座標使用百分比 (0~100)。
        
        Args:
            img: PIL Image
            name: 模板名稱（不含 .png）
            x_pct, y_pct: 左上角百分比座標
            w_pct, h_pct: 寬高百分比
        
        Returns:
            儲存路徑
        """
        x = int(x_pct * img.width / 100)
        y = int(y_pct * img.height / 100)
        w = int(w_pct * img.width / 100)
        h = int(h_pct * img.height / 100)
        
        cropped = img.crop((x, y, x + w, y + h))
        path = self._get_template_path(name)
        cropped.save(path, 'PNG')
        
        # 清除此模板的快取
        if name in self._cache:
            del self._cache[name]
        
        print(f'模板已儲存: {path} ({w}x{h})')
        return path
    
    def capture_template_from_roi(self, img, name, roi_class):
        """
        從 ROI 設定中自動擷取模板。
        roi_class 需要有 x1, y1, x2, y2 或類似屬性。
        """
        if hasattr(roi_class, 'x1') and hasattr(roi_class, 'x2'):
            x_pct = getattr(roi_class, 'x1', 0)
            y_pct = getattr(roi_class, 'y1', getattr(roi_class, 'y', 0))
            w_pct = getattr(roi_class, 'x2', 100) - x_pct
            h_pct = getattr(roi_class, 'y2', getattr(roi_class, 'y', 100)) - y_pct
            return self.capture_template(img, name, x_pct, y_pct, w_pct, h_pct)
        else:
            raise ValueError(f'ROI class {roi_class.__name__} 缺少 x1/x2 屬性')


# 全域單例
detector = TemplateDetector()
