from coreweb import get,post
import logging

from SolarLunarDatetime import convert
import datetime
from tools import GANZHI_to_num, luoshunum_to_GUA, GUA_char_to_unicode, jigong, yinyang
from gua import gua_to_yuantang, get_gua_xiantian, get_gua_houtian, get_age


GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

@get('/helo')
async def index_helo(request):

    return {
        "__template__":"helo.html"
    }

@get('/testhelo')
async def test_helo(request):
    return {
        "__template__":"testhelo.html"
    }


@post('/api/helo')
async def api_getdate(request,*, datetimestr, gender):
    print(gender, datetimestr)
    datetime_obj = datetime.datetime.strptime(datetimestr, '%Y-%m-%d %H:%M')
    logging.info("request: %s %s"%(datetimestr, gender))
    print(datetime_obj)
    ganzhi, jieqi = convert(datetime_obj)
    year = ganzhi['year']
    nums = {}
    num_tian = 0
    num_di = 0
    for key,value in ganzhi.items():
        nums[key] = GANZHI_to_num(value)
        for x in nums[key]:            
            if x % 2==1:
                num_tian += x
            else:
                num_di += x
    
    tian_guashu = num_tian_to_guashu(num_tian)
    di_guashu   = num_di_to_guashu(num_di)
    tiangua = luoshunum_to_GUA(tian_guashu)
    digua   = luoshunum_to_GUA(di_guashu)

    if tiangua=="中":
        tiangua = jigong(gua=tiangua, gender=gender, year=datetime_obj.year)
    if digua=="中":
        digua = jigong(gua=digua, gender=gender, year=datetime_obj.year)        


    gua_xiantian = get_gua_xiantian(tiangua=tiangua, digua=digua, gender=gender, yinyang=yinyang(year[0]))

    season = "阳" if jieqi<12 else "阴"
    yuantang_order, yao_bian = gua_to_yuantang(row=gua_xiantian,hour_Z=ganzhi['hour'][-1], gender=gender, season=season)

    gua_houtian  = get_gua_houtian(gua_xiantian=gua_xiantian, yao_bian=yao_bian)

    yuantang_xian = yao_bian
    yuantang_hou  = (yao_bian + 3) % 6

    age_xian, endage = get_age(gua_xiantian, yuantang=yuantang_xian)
    age_hou, _ = get_age(gua_houtian, yuantang=yuantang_hou, startage=endage)

    result_dict={
        "时间":datetime_obj.strftime("%Y-%m-%d %H:%M:%S"),
        "性别": gender,
        "yinyang":yinyang(year[0]),
        "干支":ganzhi,
        "数字":nums,
        "天数":num_tian,
        "地数":num_di,
        "天卦数":tian_guashu,
        "地卦数":di_guashu,
        "天卦": tiangua+GUA_char_to_unicode(tiangua),
        "地卦": digua+GUA_char_to_unicode(digua),
        "元堂": yuantang_order,
        "先天卦": gua_xiantian['name'] + gua_xiantian['gua'], 
        "后天卦": gua_houtian['name'] + gua_houtian['gua'],
        "先天元堂": yuantang_xian,
        "后天元堂": yuantang_hou,
        "age_xian": age_xian,
        "age_hou":  age_hou,
        "bin_xian": gua_xiantian['bin'],
        "bin_hou" : gua_houtian['bin'],
        "name_xian": gua_xiantian['name'],
        "name_hou": gua_houtian['name']
    }
    output_list = []
    for key, value in result_dict.items():
        output_list.append('{}: {}'.format(key, value))
    result_str = '\n\n'.join(output_list)
    return result_dict


def num_tian_to_guashu(x):
    if x==25:
        return 5
    while x>25:
        x-=25
    if x%10==0:
        return x//10
    else:
        return x%10

def num_di_to_guashu(x):
    if x==30:
        return 3
    while x>30:
        x-=30
    if x%10==0:
        return x//10
    else:
        return x%10