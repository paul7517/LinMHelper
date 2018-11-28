import win32gui
from re import search
import win32con
from win32ui import CreateDCFromHandle,CreateBitmap
from numpy import fromstring
from cv2 import cvtColor,COLOR_BGR2RGB
from PIL import Image
from win32gui import FindWindowEx, PostMessage, SetForegroundWindow
from time import sleep
from numpy.core.numerictypes import void
from sys import exc_info


def FindWindow_bySearch(pattern):
    window_list = []
    win32gui.EnumWindows(lambda hWnd, param: param.append(hWnd), window_list)
    for each in window_list:
        if search(pattern, win32gui.GetWindowText(each)) is not None:
            return each
 
def getWindow_W_H(hwnd):
    # 取得目標視窗的大小
    left, top, right, bot = win32gui.GetWindowRect(hwnd)
    width = right - left
    height = bot - top
    #print( left, top, right, bot)
    return (left, top, width, height)
 
def getWindow_Img(hwnd):
    # 將 hwnd 換成 WindowLong
    s = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
    win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, s | win32con.WS_EX_LAYERED)
    # 判斷視窗是否最小化
    show = win32gui.IsIconic(hwnd)
    # 將視窗圖層屬性改變成透明    
    # 還原視窗並拉到最前方
    # 取消最大小化動畫
    # 取得視窗寬高
    if show == 1: 
        win32gui.SystemParametersInfo(win32con.SPI_SETANIMATION, 0)
        win32gui.SetLayeredWindowAttributes(hwnd, 0, 0, win32con.LWA_ALPHA)
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)    
        x, y, width, height = getWindow_W_H(hwnd)        
    
    # 創造輸出圖層
    hwindc = win32gui.GetWindowDC(hwnd)
    srcdc = CreateDCFromHandle(hwindc)
    memdc = srcdc.CreateCompatibleDC()
    bmp = CreateBitmap()
    
    # 取得視窗寬高
    x, y, width, height = getWindow_W_H(hwnd)
    # 如果視窗最小化，則移到Z軸最下方
    
    if show == 1: 
        setWindowPosition(hwnd, x, y, width, height)
    
    # 複製目標圖層，貼上到 bmp
    # 會有莫名crash掉的機會，先直接try掉
    # 測了2、3天，發現並不會有重大影響
    try:
        bmp.CreateCompatibleBitmap(srcdc, width, height)
        memdc.SelectObject(bmp)
        memdc.BitBlt((0 , 0), (width, height), srcdc, (0, 0), win32con.SRCCOPY)
    except:
        print('複製圖層錯誤:' , exc_info()[0])
        return None
    
    # 將 bitmap 轉換成 np
    signedIntsArray = bmp.GetBitmapBits(True)
    imgArray = fromstring(signedIntsArray, dtype='uint8')
    imgArray.shape = (height, width, 4)  # png，具有透明度的
    
    imgArray = cvtColor(imgArray,COLOR_BGR2RGB)
    
    img=Image.fromarray(imgArray)
    
    # Crop Image , top 26 , left、right by case
    area = None
    if((img.height-26)/img.width < 0.55): #表示視窗放到最大
        noxToolsWidth = 30
        left_bound=(img.width - int((img.height-26)/0.5615) - noxToolsWidth)/2
        right_bound = left_bound + noxToolsWidth
        area=(left_bound,27,img.width-right_bound,img.height)
        #area=(0,0,img.width,img.height)
    else:
        area=(0,27,img.width,img.height)
    img=img.crop(area)
    #print('croped image size=%d x %d , rate is: %f' % (img.width,img.height,img.height/img.width))
    
    if(img.width> 1000):
        newWidth,newHeight = 1000 , int(img.height * (1000/img.width))
        img=img.resize((newWidth,newHeight))
    
    # 釋放device content
    srcdc.DeleteDC()
    memdc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwindc)
    win32gui.DeleteObject(bmp.GetHandle())
    # 還原目標屬性
    if show == 1 :
        try:
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
            win32gui.SystemParametersInfo(win32con.SPI_SETANIMATION, 1)
        except:
            void
    # 回傳圖片
    return img

def getControlID(hwnd):
    id = FindWindowEx(hwnd,0,None,None)
    id = FindWindowEx(hwnd,id,None,None)
    return id

'''
#Shell的方法，但是會影響到平常電腦操作，不建議使用
def postMessage(hwnd,key):
    ch = ['1','2','3','4','5','6','7','8','9']
    if(ch.index(key) >= 0):
        k = 0x31 + ch.index(key)
        controlID = getControlID(hwnd)
        shell = win32com.client.Dispatch("WScript.Shell")
        shell.SendKeys(key)
        win32gui.SetForegroundWindow(hwnd)
        #PostMessage(controlID,win32con.WM_KEYDOWN,k,0)
        #PostMessage(controlID,win32con.WM_KEYUP,k,0)
    else:
        print('設定的熱鍵不合法，只能為1-9')
'''
def postMessage(hwnd,key):
    ch = ['1','2','3','4','5','6','7','8','9']
    if(ch.index(key) >= 0):
        k = 0x31 + ch.index(key)
        controlID = getControlID(hwnd)
        try:
            win32gui.SetForegroundWindow(hwnd)
        except:
            void
            
        PostMessage(controlID,win32con.WM_KEYDOWN,k,0)
        PostMessage(controlID,win32con.WM_KEYUP,k,0)
    else:
        print('設定的熱鍵不合法，只能為1-9')

def setWindowPosition(hwnd,x,y,width,height):
    win32gui.SetWindowPos(hwnd, win32con.HWND_BOTTOM, x, y, width, height, win32con.SWP_NOACTIVATE)
''' Temp to Delete
def getRGB(img,x,y):
    #在array裡pixcel是[Height][Width]儲存
    #每個cell存放 BGRA
    b,g,r,a=img[y][x]
    return (r,g,b)
'''