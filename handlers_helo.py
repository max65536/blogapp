from coreweb import get,post

from SolarLunarDatetime import convert
import datetime
from tools import GANZHI_to_num, luoshunum_to_GUA, GUA_char_to_unicode


GAN = "甲乙丙丁戊己庚辛壬癸"
ZHI = "子丑寅卯辰巳午未申酉戌亥"

@get('/helo')
async def index_helo(request):

    return {
        "__template__":"helo.html"
    }

@post('/api/helo')
async def api_getdate(request,*, datetimestr):
    datetime_obj = datetime.datetime.strptime(datetimestr, '%Y-%m-%d %H:%M')
    ganzhi = convert(datetime_obj)
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

    result_dict={
        "时间":datetime_obj.strftime("%Y-%m-%d %H:%M:%S"),
        "干支":ganzhi,
        "数字":nums,
        "天数":num_tian,
        "地数":num_di,
        "天卦数":tian_guashu,
        "地卦数":di_guashu,
        "天卦": tiangua+GUA_char_to_unicode(tiangua),
        "地卦": digua+GUA_char_to_unicode(digua)
    }
    output_list = []
    for key, value in result_dict.items():
        output_list.append('{}: {}'.format(key, value))
    result_str = '\n\n'.join(output_list)
    return result_str


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