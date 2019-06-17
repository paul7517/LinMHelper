
def detectTeamEnabled(img):
    c1X , c1Y = 10.25 , 24.28
    c2X , c2Y = 27.55 , 23.85

    greyRange = (110,125)
    DarkRange = (55,70)

    #比對的點在一般畫面接近全白，故判斷RGB總合>700
    #在對話中，會變灰值會介於110至125之間
    isC1Matched = comparePointRGBSum(img, c1X , c1Y, 700, 770,-1)#-1代表不override pixel
    isC2Matched = comparePointRGBSum(img, c2X , c2Y, 700, 770,-1)#-1代表不override pixel
    isTeamEnabled = isC1Matched and isC2Matched

    isC1Grey = comparePointRGB(img , c1X , c1Y , greyRange , greyRange , greyRange , -1)
    isC2Grey = comparePointRGB(img , c2X , c2Y , greyRange , greyRange , greyRange , -1)

    isC1Dark = comparePointRGB(img , c1X , c1Y , DarkRange , DarkRange , DarkRange , 0)
    isC2Dark = comparePointRGB(img , c2X , c2Y , DarkRange , DarkRange , DarkRange , 0)

    isGrey = 0 
    if isC1Grey and isC2Grey:
        isGrey = 1
    elif isC1Dark and isC2Dark:
        isGrey = 2
        
    #isC3Matched = comparePointRGBSum(img, 17.2, 34.7, 700, 770)
    return isTeamEnabled , isGrey

def detectTeamPositionAvalible(img,teamPosition):
    x=17.2
    
    position = teamPosition
    if(position >= 1):  position-=1
    y=34.7 + 8.8*position
    
    matched = comparePointRGBSum(img, x, y, 700, 770,0)
    return matched

def detectItemSkillPanelOpened(img):
    intX=int(71.23 * img.width / 100)
    intY1=int(20.88 * img.height / 100)
    intY2=int(61.43 * img.height / 100)
    
    cnt = 0
    total = intY2-intY1
    for intY in range(intY1,intY2):
        if(compareRGB(getPixel(img, intX, intY, -1), (25,40) , (15,30) , (10,25)) 
           or compareRGB(getPixel(img, intX, intY, -1), (15,25) , (15,25) , (15,25))):
           cnt+=1
    #print(cnt / total * 100)    
    return cnt / total * 100 >= 72.0        

#判斷血條
def detectHPPercent(img,teamPosition,rgbValue):
    cnt = 0
    poisonCnt = 0
    
    debug = False
    poisonOut = ''
    
    intX1 = int(5.7 * img.width / 100)
    intX2 = int(14.1 * img.width / 100)
    
    shiftUnit = 0
    if(teamPosition != None):
        shiftUnit = int(teamPosition)
    if(shiftUnit >=1): #0代表沒組隊，但還是要判斷
        shiftUnit -=1
        
    yPercent = 35.38 + shiftUnit * 8.8
    
    y=int(yPercent * img.height /100)
    for x in range(intX1,intX2):
        rgb = getPixel(img, x, y, rgbValue)
        r = rgb[0]; g=rgb[1]; b=rgb[2]
        #outStr += '%d , %d , %d\n'  % (rgb[0],rgb[1],rgb[2]) 
        if(debug): poisonOut += 'R=%d,G=%d,B=%d\n'  % (r,g,b,)
        
        if(comparePointRGB(img, x, y, (137,205), (0,15),(0,15),rgbValue)):
            cnt+=1
        #elif(g - 20 > r and g-20 > b and r < 80 and b < 55):
        #elif(g - 20 >= r and g-20 >= b and r < 100 and b < 75):
        #背景是藍色的時候可能造成G = B或是B略大於G
        #elif(g + 20 >= r and g >= b + 20 and r < 100 and b < 75):
        elif(g + 20 >= r and g >= b - 15 and r < 100 and b < 75):
            poisonCnt += 1
            
    
    if(cnt == 0):  cnt = poisonCnt
    
    hpPercent = int(cnt / (intX2-intX1) * 100)       
    
    #中毒的時候還是會有誤判的時候，試著把誤判的情況印出來。
    if(debug and hpPercent < 50 and cnt == poisonCnt):
        print(poisonOut) 

    return hpPercent

#判斷HP條
def detectMPPercent(img,teamPosition,rgbValue):
    cnt = 0
    intX1 = int(5.7 * img.width / 100)
    intX2 = int(14.1 * img.width / 100)
    
    shiftUnit = 0
    if(teamPosition != None):
        shiftUnit = int(teamPosition)
    if(shiftUnit >=1 ): #0代表沒組隊，但還是要判斷
        shiftUnit -= 1
        
    yPercent = 37.00 + shiftUnit * 8.8
    
    y=int(yPercent * img.height /100)
    for x in range(intX1,intX2):
        if(comparePointRGB(img, x, y, (0,21), (60,125),(110,202),rgbValue)):
            cnt+=1
    
    mpPercent = int(cnt / (intX2-intX1) * 100)
    return mpPercent

#判斷是否攻擊中
def detectIsAttack(img):
    cnt = 0
    intX1 = int(83.8 * img.width / 100)
    intX2 = int(85.64 * img.width / 100)
    y = int(69.07 * img.height / 100)
    for x in range(intX1,intX2):
        isNearAttck = comparePointRGB(img, x, y, (230,255), (200,255), (130,255),-1)
        #isFarAttck = comparePointRGB(img, x, y, (90,250), (70,150), (0,90),0)
        isFarAttck = comparePointRGB(img, x, y, (140,255), (70,170), (0,110),0)
        if(isNearAttck or isFarAttck):
            cnt+=1
        y+=1
    
    attRate = cnt / (intX2 - intX1 + 1) * 100 
    #print('attRate:',attRate)

    return attRate >= 60

#判斷是否被攻擊
def detectIsAttacked(img):
    cnt = 0
    intX1 = int(0.5 * img.width / 100)
    intX2 = int(5.0 * img.width / 100)
    y = int(1.0*img.height / 100)
    for x in range(intX1,intX2):
        if(comparePointRGB(img, x, y, (90,255), (0,25), (0,25), 255)):
            cnt+=1
    
    matchPercent = int(cnt / (intX2 - intX1 + 1) * 100)
    if(matchPercent >= 50):
        return True

#比較單點的RGB總合
def comparePointRGBSum(img,x,y,rgb_bound1,rgb_bound2,overrideValue):
    intX , intY = convertIntPosition(img,x,y)
        
    r,g,b = getPixel(img, intX, intY, overrideValue)
    rgbSum = r + g + b
    return rgbSum >= rgb_bound1 and rgbSum <= rgb_bound2

#比對單點的R、G、B範圍
def comparePointRGB(img,x,y,r_range,g_range,b_range,rgbValue):
    intX , intY = convertIntPosition(img,x,y)

    rgb = getPixel(img, intX, intY, rgbValue)
    rst = compareRGB(rgb, r_range, g_range, b_range)
    
    if(rgbValue== -2):
        if(not rst):
            print('RGB:%d,%d,%d , Range is %d~%d,%d~%d,%d~%d' %(rgb[0],rgb[1],rgb[2],r_range[0],r_range[1],g_range[0],g_range[1],b_range[0],b_range[1]))
    return rst

def convertIntPosition(img,fX,fY):
    if isinstance(fX,float) and isinstance(fY,float):
        intX , intY = int(fX * img.width / 100) , int(fY * img.height / 100) 
    else:
        intX , intY = fX , fY
    
    return intX , intY

#取得img裡的pixel rgb (主要用以在圖上mark)
def getPixel(img,intX,intY,rgbValue):
    rgb = img.getpixel((intX,intY))
    
    #work around
    if(rgbValue == -2):
        print(rgb)
    
    if(rgbValue >= 0):
        img.putpixel((intX,intY-1),(rgbValue,rgbValue,rgbValue))
        #img.putpixel((intX,intY+1),(rgbValue,rgbValue,rgbValue))
    return rgb

#比對RGB是否有在range裡
def compareRGB(rgb , r_range,g_range,b_range):
    return (rgb[0] >= r_range[0] and r_range[1]) and (rgb[1] >=g_range[0] and rgb[1] <= g_range[1]) and (rgb[2] >= b_range[0] and rgb[2] <= b_range[1])