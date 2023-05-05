import sxtwl # 阴历日期转换库
from consts import GAN, ZHI, YUEJIANG, JIEQI, mapping_JIEQI_to_YUEJIANG 
import datetime

from pytz import timezone
from IPython import embed

def datetime_as_timezone(date_time, time_zone):
    tz = timezone(time_zone)
    utc = timezone('UTC')
    return date_time.replace(tzinfo=utc).astimezone(tz)

def convert(time=None, time_zone='Asia/Shanghai'):
    if time is None:
        date_time = datetime.datetime.now()
    else:
        date_time = time        
    # local_date_time = datetime_as_timezone(date_time=date_time, time_zone=time_zone)
    local_date_time = date_time
    solartime = SolarLunarDatetime.init_from_solar(local_date_time.year, local_date_time.month, local_date_time.day, local_date_time.hour)
    # embed()
    return solartime.GanZhi, solartime.JieQi


class SolarLunarDatetime(object):

    def __init__(self, day_object, hour):
        '''
        day_object(sxtwl.day)
        '''
        self.date = day_object
        self.hour = hour
        self.GanZhi = self.get_GanZhi(self.date, self.hour)
        self.YueJiang = self.get_YueJiang(self.date)

    def get_YueJiang(self, date):
        i = 0 
        day = date
        jieqi = -1
        while True:
            # hasJieQi的接口比getJieQiJD速度要快，你也可以使用getJieQiJD来判断是否有节气。
            if day.hasJieQi():
                jieqi = day.getJieQi()
                break
            # 这里可以使用after或者before，不用担心速度，这里的计算在底层仅仅是+1这么简单
            day = day.before(1)
            i += 1
            if i > 30:
                print("YueJiang not found")
                return -1
        self.JieQi = jieqi
        return YUEJIANG[mapping_JIEQI_to_YUEJIANG[jieqi]]
        

    def get_GanZhi(self, date, hour, is_boundary_chunjie=False, separate_ZiShi=False):
        '''
        is_boundary_chunjie(bool) : True以春节为界, False以立春为界
        separate_ZiShi(bool) : 是否分早晚子时
        '''
        hourGZ  = date.getHourGZ(hour)
        if hour==23 and not separate_ZiShi:
            dayGZ   = date.after(1).getDayGZ()
        else:
            #分早晚子时
            dayGZ   = date.getDayGZ()

        monthGZ = date.getMonthGZ()
        yearGZ  = date.getYearGZ(is_boundary_chunjie)

        GanZhi = {}
        GanZhi["hour"]  = GAN[hourGZ.tg]  + ZHI[hourGZ.dz]
        GanZhi["day"]   = GAN[dayGZ.tg]   + ZHI[dayGZ.dz]
        GanZhi["month"] = GAN[monthGZ.tg] + ZHI[monthGZ.dz]
        GanZhi["year"]  = GAN[yearGZ.tg]  + ZHI[yearGZ.dz]
        return GanZhi


    @classmethod
    def init_from_solar(cls, year, month, day, hour):
        solar_day = sxtwl.fromSolar(year, month, day)
        return cls(solar_day, hour)

    @classmethod
    def init_from_lunar(cls, year, month, day, hour):
        '''
        从 阴历年月日时 转到 阳历年月日时 和 干支
        '''
        lunar_day = sxtwl.fromLunar(year, month, day)
        return cls(lunar_day, hour)

    @property
    def solar_datetime(self):
        date = self.date
        return {"year": date.getSolarYear(), "month": date.getSolarMonth(), 
                "day": date.getSolarDay(), "hour": self.hour}

    @property
    def lunar_datetime(self, is_boundary_chunjie=False):
        date = self.date
        return {"year": date.getLunarYear(is_boundary_chunjie), "month": date.getLunarMonth(), 
                "day": date.getLunarDay(), "hour": self.hour}

'''
月将起法：
雨水前日卯初刻，太阳入卫用登明，（亥）
春分后二巳一刻，入鲁河魁作将明，（戌）
谷雨后四亥初刻，入赵从魁用可称，（酉）
小满后五酉三刻，入晋还须传送兵，（申）
夏至后四未一刻，入秦小吉用其名；（未）
大暑后三巳一刻，入周先用胜光灵，（午）
处暑后三巳二刻，入楚还当太乙迎，（巳）
秋分后七寅三刻，入郑天罡用去亨，（辰）
霜降后九丑三刻，太冲运动宋州城，（卯）
小雷后七戌一刻，功曹将领入燕京：（寅）
冬至后四亥一刻，入吴大吉便休停，（丑）
大寒当日酉三刻，入齐神后岁功成。（子）

正月雨水后月将为亥，名登明。
二月春分后月将为戌，名河魁。
三月谷雨后月将为酉，名从魁。
四月小满后月将为申，名传送。
五月夏至后月将为未，名小吉。
六月大暑后月将为午，名胜光。
七月处暑后月将为巳，名太乙。
八月秋分后月将为辰，名天罡。
九月霜降后月将为卯，名太冲。
十月小雪后月将为寅，名功曹。
十一冬至月后月将为丑，名大吉。
十二月大寒后月将为子，名神后。

正月，北斗勺柄指向寅，月建为寅；在雨水节气后，太阳落山处于二十八宿室、壁亥宫，故月将为登明亥
二月，北斗勺柄指向卯，月建为卯；在春分节气后，太阳落山处于二十八宿奎、娄戌宫，故月将河魁戌
三月，北斗勺柄指向辰，月建为辰；在谷雨节气后，太阳落山处于二十八宿胃、昴、毕酉宫，故月将从魁酉
四月，北斗勺柄指向巳，月建为巳；在小满节气后，太阳落山处于二十八宿觜、参申宫，故月将传送申
五月，北斗勺柄指向午，月建为午；在夏至节气后，太阳落山处于二十八宿井、鬼未宫，故月将小吉未
六月，北斗勺柄指向未，月建为未；在大暑节气后，太阳落山处于二十八宿柳、星、张午宫，故月将胜光午
七月，北斗勺柄指向申，月建为申；在处暑节气后，太阳落山处于二十八宿翼、轸巳宫，故月将太乙巳
八月，北斗勺柄指向酉，月建为酉；在秋分节气后，太阳落山处于二十八宿角、亢辰宫，故月将天罡辰
九月，北斗勺柄指向戌，月建为戌；在霜降节气后，太阳落山处于二十八宿氐、房、心卯宫，故月将太冲卯
十月，北斗勺柄指向亥，月建为亥；在小雪节气后，太阳落山处于二十八宿尾、箕寅宫，故月将功曹寅
冬月，北斗勺柄指向子，月建为子；在冬至节气后，太阳落山处于二十八宿斗、牛丑宫，故月将大吉丑
腊月，北斗勺柄指向丑，月建为丑；在大寒节气后，太阳落山处于二十八宿女、虚、危子宫，故月将神后子
'''
#JieQi = ["冬至", "小寒", "大寒", "立春", "雨水", "惊蛰", "春分", "清明", "谷雨", "立夏", "小满", "芒种", "夏至", "小暑", "大暑", "立秋", "处暑","白露", "秋分", "寒露", "霜降", "立冬", "小雪", "大雪"]
#mapping [    10,     10,     11,     11,    0  ,     0 ,     1 ,     1 ,     2 ,     2 ,     3 ,     3 ,     4 ,     4 ,     5 ,     5 ,     6 ,    6 ,     7 ,     7 ,     8 ,     8 ,     9 ,     9 ]
if __name__=="__main__":
    print(convert())