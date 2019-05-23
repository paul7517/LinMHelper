from enum import Enum

#所有x,y值皆在1280x720 mode下取得
class LinMKeySet(Enum):
    #左上角的按鈕
    characterKey = [45,30]

    #底下4+1+4按鈕
    key1 = [540 , 635]
    key2 = [620 , 635]
    key3 = [700 , 635]
    key4 = [780 , 635]
    questSkill = [875,635]
    key5 = [970 , 635]
    key6 = [1050 , 635]
    key7 = [1130 , 635]
    key8 = [1210 , 635]

    #右上方選單鍵
    bossQuest = [850 , 40]
    upperShop = [930 , 40]
    upperitem = [1010 , 40]
    upperSkill = [1080 , 40]
    upperQuest = [1160 , 40]
    upperMain = [1240 , 45]

    questBtn = [930 , 185]
    questTab1 = [80 , 210]
    questTab2 = [80 , 290]
    questTab3 = [80 , 360]

    #任務/副本 1 ~ 6
    questBtn1 = [295 , 330]
    questBtn2 = [465 , 330]
    questBtn3 = [645 , 330]
    questBtn4 = [825 , 330]
    questBtn5 = [1000 , 330]
    questBtn6 = [1180 , 330]

    #接收任務對話，按同意
    acceptQuest = [740 , 545]

    #右下角auto鍵
    autoBtn = [970 , 510]

    #僅驗證補充任務次數介面
    cancelBtn = [525 , 590]

'''
print(LinMKeySet.autoBtn)
#print(dir(LinMKeySet))
print(LinMKeySet.autoBtn in LinMKeySet)
print(isinstance(LinMKeySet.autoBtn , LinMKeySet))
'''