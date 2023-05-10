import pandas as pd
from IPython import embed
gua_xiantian = "乾兑离震巽坎艮坤"
xiang_xiantian = "天澤火雷風水山地"
unicode_xiantian = "☰☱☲☳☴☵☶☷"
mapping_gua_xiang = dict(zip(gua_xiantian, xiang_xiantian))

gua_bin   = "☰☴☲☶☱☵☳☷"
xiang_bin = "天風火山澤水雷地"
mapping_xiang_idx = dict(zip(xiang_bin,range(8)))

YANG = 0
YIN  = 1

df = pd.read_csv('gua64.csv', dtype={6:str})

def get_gua_xiantian(tiangua, digua, gender, yinyang):
    if (gender=="男" and yinyang=="阳") or (gender=="女" and yinyang=="阴"):
        up   = tiangua
        down = digua
    if (gender=="男" and yinyang=="阴") or (gender=="女" and yinyang=="阳"):        
        up   = digua
        down = tiangua        
    up   = mapping_gua_xiang[up]
    down = mapping_gua_xiang[down]        
    gua_xiantian = df[(df['up']==up)& (df['down']==down)].iloc[0]
    return gua_xiantian

def get_gua_houtian(gua_xiantian, yao_bian):
    gua_bian_num = (1 << yao_bian) ^ gua_xiantian['yao']
    houtian_num  = ((gua_bian_num % 8) << 3) | (gua_bian_num >> 3)
    gua_houtian = df[df['yao']==houtian_num].iloc[0]    
    return gua_houtian

def gua_to_yao(row):
    yao = mapping_xiang_idx[row['up']] << 3 | mapping_xiang_idx[row['down']]
    # 其中，: 表示格式说明符的开始，0 表示填充的字符是 '0'，> 表示字符串对齐方式是右对齐（默认为左对齐），8 表示字符串的总长度为 8。
    bin_str = '{:0>6}'.format(bin(yao)[2:])[::-1]
    return bin_str

def gua_to_yuantang(row, hour_Z=None, gender="男", season=None):    
    '''
    定元堂
    '''
    # up   = mapping_gua_xiang[up]
    # down = mapping_gua_xiang[down]
    # row = df[(df['up']==up)& (df['down']==down)].iloc[0]
    # print(row)

    def put(shi, where):
        for i in range(6):
            if row_bin[i]==str(where):
                try:
                    order[i] += shi.pop() 
                except IndexError:
                    break

    yangshi = list("子丑寅卯辰巳")[::-1]
    yinshi  = list("午未申酉戌亥")[::-1]
    row_bin = row['bin']

    # print(row_bin)

    order = [''] * 6
    # 阳为0 阴为1
    # yinyang=0
    yinyang = 0 if hour_Z in yangshi else 1
    # print(row_bin)

    if (row['name']=="乾"):
        if gender=="男":
            order = ['子卯', '丑辰', '寅巳', '午酉', '未戌', '申亥']
        elif gender=="女" and season=="阳":
            order = ['申亥', '未戌', '午酉', '寅巳', '丑辰', '子卯']
        elif gender=="女" and season=="阴":
            order = ['子卯', '丑辰', '寅巳', '午酉', '未戌', '申亥']

    elif (row['name']=="坤"):
        if gender=="女":
            order = ['子卯', '丑辰', '寅巳', '午酉', '未戌', '申亥']
        elif gender=="男" and season=="阴":
            order = ['申亥', '未戌', '午酉', '寅巳', '丑辰', '子卯']
        elif gender=="男" and season=="阳":
            order = ['子卯', '丑辰', '寅巳', '午酉', '未戌', '申亥']

    elif yinyang==0:
        yang_num  = row_bin.count('0')
        if yang_num==1 or yang_num==2:
            put(yangshi, where=YANG)
            put(yangshi, where=YANG)
            put(yangshi, where=YIN)

        elif yang_num==3:
            put(yangshi, where=YANG)
            put(yangshi, where=YANG)            
                
        elif yang_num==4 or yang_num==5:
            put(yangshi, where=YANG)
            put(yangshi, where=YIN)
    else:
        yin_num  = row_bin.count('1')
        if yin_num==1 or yin_num==2:
            put(yinshi, where=YIN)
            put(yinshi, where=YIN)
            put(yinshi, where=YANG)

        elif yin_num==3:
            put(yinshi, where=YIN)
            put(yinshi, where=YIN)            
                
        elif yin_num==4 or yin_num==5:
            put(yinshi, where=YIN)
            put(yinshi, where=YANG)
    # embed()
    yao_bian = -1
    for i, item in enumerate(order):
        if hour_Z in item:
            yao_bian = i
            break
    print(order, hour_Z, yao_bian, row_bin, row)
    assert yao_bian >= 0
    # gua_bian_num = (1 << yao_bian) ^ row['yao']
    # gua_bian = df[df['yao']==gua_bian_num].iloc[0]

    return order, yao_bian

def zhizungua(gua):
    '''
    至尊卦
    '''
    pass

    
def get_age(gua, yuantang, startage=0):
    start = yuantang
    bin = gua['bin']
    age_list = [0] * 6
    i = start
    age = startage
    while True:
        if bin[i]=='0': # yang
            age += 9
        else:
            age += 6
        age_list[i] = age
        i = (i + 1) % 6
        if i==yuantang:
            break
    return age_list, age

# def get_gua_nian(gua, yuantang, startage=0):
#     gua_year(gua=gua, yaobian=, yinyang=)

def shi_ying(gua):
    '''
    求世爻应爻

    寻宫问世诀
    天同二世天变五，地同四世地变初，
    本宫六世三世异，人同游魂人变归。
    一二三六外卦宫，四五游魂内变更，
    归魂内卦是本宫。
    '''

    yao = gua['bin']
    down = yao[:3]
    up = yao[3:]

    tian = up[2]==down[2]
    ren  = up[1]==down[1]
    di   = up[0]==down[0]        
    if not di and not ren and     tian: # 天同
        shi = 2 - 1
    if     di and     ren and not tian: # 天变            
        shi = 5 - 1    

    if     di and not ren and not tian: # 地同
        shi = 4 - 1
    if not di and     ren and     tian: # 地变
        shi = 1 - 1        

    if     di and     ren and     tian: # 本宫
        shi = 6 - 1
    if not di and not ren and not tian: # 三世异
        shi = 3 - 1                

    if not di and     ren and not tian: # 人同
        shi = 4 - 1
    if     di and not ren and     tian: # 人变
        shi = 3 - 1        

    ying = (shi + 3) % 6
    return shi, ying

def gua_year(gua, yaobian, yinyang):

    start_bin = gua['bin']
    current_bin = start_bin

    def next(x, increase):
        return (x+increase) % 6
    
    def bin_change(i):     
        nonlocal current_bin           
        if current_bin[i]=='0':
            new_bin = current_bin[:i] + '1' + current_bin[i+1:]
        elif current_bin[i]=='1':
            new_bin = current_bin[:i] + '0' + current_bin[i+1:]
        search = df[df['bin']==new_bin].iloc[0]
        # print(i, current_bin, new_bin, search['name'], search['gua'])   
        current_bin = new_bin     
        return new_bin



    gua_list = []
    if yinyang==YIN or current_bin[yaobian]=='1':
        gua_list.append(bin_change(yaobian))
    else:
        gua_list.append(current_bin)

    if start_bin[yaobian]=='0':
        gua_list.append(bin_change(next(yaobian, 3)))
        gua_list.append(bin_change(yaobian))
        for i in range(6):
            yaobian = (yaobian + 1) % 6
            gua_list.append(bin_change(yaobian))
    else:
        for i in range(5):
            yaobian = (yaobian + 1) % 6
            gua_list.append(bin_change(yaobian))    

    # name_list = [df[df['bin']==x].iloc[0] for x in gua_list]    
    return gua_list

if __name__=="__main__":
# 读取表格

# df.drop('bin', inplace=True, axis=1)
# df['bin'] = df.apply(gua_to_yao, axis=1)

# 将表格保存为csv
# df.to_csv('gua642.csv', index=False)
# print(mapping_xiang_idx)
    gender = "男"
    tiangua = "离"
    digua   = "艮"
    gua_xiantian = get_gua_xiantian(tiangua=tiangua, digua=digua, gender=gender, yinyang="阳")

    yuantang_order, yao_bian = gua_to_yuantang(row=gua_xiantian,hour_Z="子", gender=gender, )

    gua_houtian  = get_gua_houtian(gua_xiantian=gua_xiantian, yao_bian=yao_bian)

    yuantang_xian = yao_bian
    yuantang_hou  = (yao_bian + 3) % 6
    # order = gua_to_yuantang("乾", down="乾", hour_Z="丑", gender="男", season=None)
    # print(order)
    age_xian, endage = get_age(gua_xiantian, yuantang=yuantang_xian)
    age_hou, _ = get_age(gua_houtian, yuantang=yuantang_hou, startage=endage)
    print("先天：", gua_xiantian.iloc[0], "元堂:", yuantang_xian)
    print(age_xian)
    print("后天：", gua_houtian.iloc[0],  "元堂:", yuantang_hou)
    print(age_hou)

    gua_list = gua_year(df[df['name']=='同人'].iloc[0], 2, 1)  
    print(gua_list)
    
    # embed()