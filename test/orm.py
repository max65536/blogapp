#要编写一个ORM框架，所有的类都只能动态定义，因为只有使用者才能根据表的结构定义出对应的类来。
import asyncio, logging,time

import aiomysql
def log(sql,args=()):
    logging.info('SQL:%s' %sql)

async def create_pool(loop,**kw):
    logging.info('create database: connecting pool...')
    global __pool
    __pool= await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )

async def destroy_pool():
    global __pool
    if __pool is not None :
        __pool.close()
        await __pool.wait_closed()

async def execute(sql,args):
    log(sql)
    with(await __pool)as conn:
        try:
            cur= await conn.cursor()
            await cur.execute(sql.replace('?','%s'),args)
            affected=cur.rowcount
            await cur.close()
        except BaseException as e:
            raise
        return affected

async def select(sql,args,size=None):
    log(sql,args)
    global __pool
    async with __pool.get() as conn:
        async with conn.cursor(aiomysql.DictCursor) as cur:
        # SQL语句的占位符是?，而MySQL的占位符是%s
            await cur.execute(sql.replace('?','%s'),args or ())
            if size:
                rs= await cur.fetchmany(size)
            else:
                rs=await cur.fetchall()
        # await cur.close()
        logging.info('rows returned: %s' %len(rs))
        return rs

def create_args_string(num):
    lol=[]
    for n in range(num):
        lol.append('?')
    return (','.join(lol))



class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)

# StringField, BooleanField, FloatField, TextField
class StringField(Field):
    def __init__(self, name=None, primary_key=False, default=None, ddl='varchar(100)'):
        super().__init__(name, ddl, primary_key, default)

class BooleanField(Field):
    def __init__(self, name=None, default=False):
        super().__init__(name, 'boolean', False, default)

class IntegerField(Field):
    def __init__(self, name=None,primary_key=False,default=0):
        super().__init__(name, 'int', primary_key, default)

class FloatField(Field):
    """docstring for FloatField"""
    def __init__(self, name=None,primary_key=False,default=0.0):
        super().__init__(name,'float',primary_key,default)

'''
MyClass = MetaClass()    #元类创建
MyObject = MyClass()     #类创建实例
实际上MyClass就是通过type()来创创建出MyClass类，它是type()类的一个实例；同时MyClass本身也是类，也可以创建出自己的实例，这里就是MyObject
'''
# 请记住，'type'实际上是一个类，就像'str'和'int'一样。所以，你可以从type继承
# __new__ 是在__init__之前被调用的特殊方法，__new__是用来创建对象并返回之的方法，__new_()是一个类方法
# 而__init__只是用来将传入的参数初始化给对象，它是在对象创建之后执行的方法。
# 你很少用到__new__，除非你希望能够控制对象的创建。这里，创建的对象是类，我们希望能够自定义它，所以我们这里改写__new__
# 如果你希望的话，你也可以在__init__中做些事情。还有一些高级的用法会涉及到改写__call__特殊方法，但是我们这里不用，下面我们可以单独的讨论这个使用
class ModelMetaclass(type):
    # cls:代表要__init__的类，此参数在实例化时由Python解释器自动提供(例如下文的User和Model)
    # bases：代表继承父类的集合
    # attrs：类的方法集合
    def __new__(cls,name,bases,attrs):
        if name=='Model':
            return type.__new__(cls,name, bases, attrs)
        tableName=attrs.get('__table__',None) or name
        logging.info('found table: %s (table: %s)'%(name,tableName))
        mappings=dict()
        fields=[]#field保存的是除主键外的属性名
        primaryKey=None
        #k表示字段名
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info('Found mapping %s==>%s' %(k,v))
                mappings[k]=v
                if v.primary_key:
                    logging.info('found primaryKey')
                    if primaryKey:
                        raise RuntimeError('Duplicated key for field')
                    primaryKey=k
                else:
                    fields.append(k)
        if not primaryKey:
            RuntimeError('primaryKey not found')
        # w下面位字段从类属性中删除Field 属性
        #将类属性移除，使定义的类字段不污染User类属性，只在实例中可以访问这些key
        for k in mappings.keys():
            attrs.pop(k)
        #????????????????????为何要删除k？
        # 将除主键外的其他属性变成`id`, `name`这种形式，关于反引号``的用法，可以参考点击打开链接
        escaped_fields=list(map(lambda f:'`%s`' %f, fields))
        #?????
        #'abc'=>'`%abc`'
        # 保存属性和列的映射关系
        attrs['__mappings__']=mappings
        # 保存表名
        attrs['__table__']=tableName  #这里的tablename并没有转换成反引号的形式
        # 保存主键名称
        attrs['__primary_key__']=primaryKey
        # 保存主键外的属性名
        attrs['__fields__']=fields
        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)


        '''
        要创建一个class对象，type()函数依次传入3个参数：

        1.class的名称；
        2.继承的父类集合，注意Python支持多重继承，如果只有一个父类，别忘了tuple的单元素写法；
        3.class的方法名称与函数绑定，这里我们把函数fn绑定到方法名hello上。

        __new__()方法接收到的参数依次是：
        1.当前准备创建的类的对象；
        2.类的名字；
        3.类继承的父类集合；
        4.类的方法集合。
        '''
        return type.__new__(cls,name,bases,attrs)

class Model(dict, metaclass=ModelMetaclass):
    def __init__(self,**kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self,key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError("'Model' object have no attribution %s"%key)

    def __setattr__(self,key,value):
        self[key]=value

    def getValue(self,key):
        return getattr(self,key,None)

    def getValueOrDefault(self,key):
        value=getattr(self,key,None)
        if value is None:
            field=self.__mappings__[key]
            if field.default is not None:
                value=field.default() if callable(field.default) else field.default
                #???????
                logging.debug('using default value for %s:%s'%(key,str(value)))
                setattr(self,key,value)
        return value

    #获取表里符合条件的所有数据,类方法的第一个参数为该类名
    #类方法实例和类都可以直接调用
    #类方法用在模拟java定义多个构造函数的情况。由于python类中只能有一个初始化方法，不能按照不同的情况初始化类。
    #cls参数是自动传入的
    @classmethod
    async def find(cls,pk):
        'find object by primaryKey'
        rs=await select('%s where `%s`=?'%(cls.__select__,cls.__primary_key__),[pk],1)
        if len(rs)==0:
            return None
        return cls(**rs[0])
    async def save(self):
        args=list(map(self.get))

    @classmethod
    async def findAll(cls,**kw):
        rs=[]
        if len(kw)==0:
            rs=await select(cls.__select__,None)
        else:
            args=[]
            values=[]
            for k,v in kw.items():
                args.append('%s=?'%k)
                values.append(v)
            print('%s where %s'%(cls.__select__,'and'.join(args),values))
        return rs

    async def save(self):
        args=list(map(self.getValueOrDefault,self.__fields__))
        print('save"%s'%args)
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows=await(execute(self.__insert__,args))
        if rows!=1:
            print(self.__insert__)
            logging.warning('failed to insert record: affected rows:%s'%rows)
# user=User(id=123,name='Michael')
# user.insert()
# users=User.findAll()
class User(Model): #虽然User类乍看没有参数传入，但实际上，User类继承Model类，Model类又继承dict类，所以User类的实例可以传入关键字参数
    __table__='users'
    id = IntegerField('id',primary_key=True) #主键为id， tablename为User，即类名
    name = StringField('name')
    email = StringField('email')
    passwd = StringField('passwd')
    admin=BooleanField()
    image=StringField('image')
    created_at = FloatField(default=time.time)
#以下为测试

loop1 = asyncio.get_event_loop()
async def test():
    # await destroy_pool()
    await create_pool(loop=loop1,host='localhost',port=3306,user='root',password='root',db='awesome')
    u = User(id=1,name='Test3', email='tefasf@example.com', passwd='1234567890', image='about:blank')
    await u.save()
    r=await User.findAll()
    print(r)
    await destroy_pool()

loop1.run_until_complete(test())

