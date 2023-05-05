from consts import GAN, ZHI, YUEJIANG, JIEQI, mapping_JIEQI_to_YUEJIANG, WUXING, YUEJIANG_to_NAME

def circle_substract(a, b, n):
    '''
    rtype tuple (count_left(-), count_right(+))
    '''
    res = a - b
    if res<0:
        return (res, res+n)
    elif res>0:
        return (res-n, res)
    elif res==0:
        return (0, 0)

def relative_pos(a, b, lst):
    '''
    计算list中两个元素相对位置: a - b
    '''
    assert a in lst
    assert b in lst
    return circle_substract(lst.index(a), lst.index(b), len(lst))

def GANZHI_to_WUXING(x):
    # GAN         = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
    # ZHI         = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
    GAN_to_WUXING = ["木", "木", "火", "火", "土", "土", "金", "金", "水", "水" ]
    ZHI_to_WUXING = ["水", "土", "木", "木", "土", "火", "火", "土", "金", "金", "土", "水"]
    if x in GAN:
        return GAN_to_WUXING[GAN.index(x)]
    if x in ZHI:
        return ZHI_to_WUXING[ZHI.index(x)]
    assert x in WUXING
    return x

def WUXING_to_num(x):
    mapping_WUXING_to_NUM = {"金":[4,9], "木":[3,8], "水":[1,6], "火":[2,7], "土":[5,10]}
    return mapping_WUXING_to_NUM[x]

def GAN_to_num(x):
    mapping_GAN_to_NUM = {"甲":6,"乙":2,"丙":8,"丁":7,"戊":1,"己":9,"庚":3,"辛":4,"壬":6,"癸":2}
    return mapping_GAN_to_NUM[x]

def ZHI_to_num(x):
    assert x in ZHI
    wuxing = GANZHI_to_WUXING(x)
    return WUXING_to_num(wuxing)

def GANZHI_to_num(x):
    assert len(x)==2
    assert x[0] in GAN
    assert x[1] in ZHI
    return [*[GAN_to_num(x[0])], *ZHI_to_num(x[1])]

def GUA_to_num(x):
    mapping_GUA_to_NUM = {"乾":6,"坤":2,"兑":7,"艮":8,"离":9,"坎":1,"震":3,"巽":4}
    return mapping_GUA_to_NUM[x]

def luoshunum_to_GUA(x):
    mapping_NUM_to_GUA = {6:"乾",2:"坤",7:"兑",8:"艮",9:"离",1:"坎",3:"震",4:"巽",5:"中"}
    return mapping_NUM_to_GUA[x]

def GUA_char_to_unicode(x):
    mapping_char_to_unicode = {"乾":"☰","坤":"☷","兑":"☱","艮":"☶","离":"☲","坎":"☵","震":"☳","巽":"☴"}
    return mapping_char_to_unicode[x]

def shengke_WUXING(a, b):
    '''
    计算干支或五行的生克
    '''
    # ["木", "火", "土", "金", "水"]
    a = GANZHI_to_WUXING(a)
    b = GANZHI_to_WUXING(b)
    try:
        dst = relative_pos(a, b, WUXING)
    except AssertionError:
        return 0
    if dst==(-1, 4):
        shengke = "生"
    elif dst==(-2, 3):
        shengke = "克"
    else:
        shengke = 0
    return shengke

def WUXING_guanxi(other, base):
    '''
    计算干支或五行的关系
    a [同，我生，生我，克我，我克] b
    a [王，相，休，  囚，  死] b
    '''
    other = GANZHI_to_WUXING(other)
    base  = GANZHI_to_WUXING(base)
    # lst = ["兄", "父", "官", "财", "子"]
    lst =   ["同", "生我", "克我", "我克", "我生"]
    try:
        dst_neg, dst_pos = relative_pos(base, other, WUXING) # base - other
    except AssertionError:
        return None
    return lst[dst_pos]


def xunshou(dayGZ):
    '''
    根据日干支查找旬首
    :param str(2) dayGZ
    '''
    gan_pos = GAN.index(dayGZ[0])
    zhi_pos = ZHI.index(dayGZ[1])
    return "甲" + ZHI[(zhi_pos - gan_pos) % 12]

def kongwang(dayGZ):
    '''
    根据日干支查找空亡
    :param str(2) dayGZ
    '''
    gan_pos = GAN.index(dayGZ[0])
    zhi_pos = ZHI.index(dayGZ[1])
    return ZHI[(zhi_pos - gan_pos -2) % 12] + ZHI[(zhi_pos - gan_pos -1) % 12]

def xundun(dayGZ, zhi):
    '''
    六甲旬遁, 根据日干支查找这一旬中支对应的干
    :param str(2) dayGZ
    :param str zhi
    '''
    xs = xunshou(dayGZ)
    distance_neg, distance_pos = relative_pos(zhi, xs[1], ZHI)
    if distance_pos>=10: # distance = 10 or 11 空亡
        return "〇"
    else:
        return GAN[distance_pos]

def liuqin(other, base):
    '''
    取六亲: 
    :rtype: str other是base的什么六亲
    '''
    # ["木", "火", "土", "金", "水"]
    # base - other = [0, 1, 2, 3, 4]
    #              = [0,-4,-3,-2,-1]
    lst            = ["兄", "父", "官", "财", "子"]
    base  = GANZHI_to_WUXING(base)
    other = GANZHI_to_WUXING(other)
    try:
        dst_neg, dst_pos = relative_pos(base, other, WUXING) # base - other
    except AssertionError:
        return None
    return lst[dst_pos]

def shishen(other, base):
    '''
    取十神: 
    同性如阳克阳为强克, 异性为弱克
    同性生为偏，异性生为正
    '''
    other_wuxing = GANZHI_to_WUXING(other)
    base_wuxing  = GANZHI_to_WUXING(base)
    same_yinyang = ["比肩", "偏印", "七杀", "偏财", "食神"]
    diff_yinyang = ["劫财", "正印", "正官", "正财", "伤官"]
    # lst = ["兄", "父", "官", "财", "子"]
    # lst =   ["同"， "生我", "克我", "我克", "我生"]
    try:
        dst_neg, dst_pos = relative_pos(base_wuxing, other_wuxing, WUXING) # base - other
    except AssertionError:
        return None
    if yinyang(other)==yinyang(base):
        return same_yinyang[dst_pos]
    else:
        return diff_yinyang[dst_pos]


def yinyang(x):
    yang = ["甲", "丙", "戊", "庚", "壬"] + ["子", "寅", "辰", "午", "申", "戌"]
    yin  = ["乙", "丁", "己", "辛", "癸"] + ["丑", "卯", "巳", "未", "酉", "亥"]
    if x in yang:
        return "阳"
    elif x in yin:
        return "阴"
    else:
        raise ValueError("value Error:" + str(x))


def wrap_color(x):
    x_wuxing = GANZHI_to_WUXING(x)
    WUXING_to_color = {"木":32,"火":31 ,"土":33,"金":93,"水":34}
    color_code = WUXING_to_color[x_wuxing]
    control_head = "\033[%dm" % color_code
    control_end  = "\033[0m"
    return ' '.join([control_head, x, control_end]) 

def yuejiang_name(yuejiang):
    return YUEJIANG_to_NAME[yuejiang]

def sizhu_to_string(sizhu):
    return sizhu['year'] + sizhu['month'] + sizhu['day'] + sizhu['hour']

def Yuan(year):
    base = 1864
    res = (year - base) // 60 % 3
    return res

def jigong(gua, gender, year):

    assert gua=="中"
    yinyang = year % 2
    yuan = Yuan(year)
    if yuan==0:    # 上元
        if gender=="男":
            return "艮"
        else: 
            return "坤"
                
    elif yuan==1:  # 中元
        if yinyang==0 and gender =="男": # 阳    
            return "艮"
        if yinyang==1 and gender =="男": # 阴    
            return "坤"
        if yinyang==0 and gender =="女": # 阳    
            return "坤"
        if yinyang==1 and gender =="女": # 阴    
            return "艮"                        
    else: # 下元
        
        assert yuan==2
        if gender=="男":            
            return "离"
        else: 
            return "兑"
