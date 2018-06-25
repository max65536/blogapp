import asyncio, logging

import aiomysql

async def create_pool(loop,**kw):
    logging.info('create database: connecting pool...')
    global __pool
    __pool= await aiomysql.create_pool(
        host=kw.get('host', 'localhost'),
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf-8'),
        autocomit=kw.get('autocomit',True),
        maxsize=kw.get('maxsize',10),
        minisize=kw.get('minisize',1),
        loop=loop
    )

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
    with (await __pool)as conn:
        cur=await conn.cursor(aiomysql.DictCursor)
        # SQL语句的占位符是?，而MySQL的占位符是%s
        await cur.execute(sql.replace('?','%s'),args or ())
        if size:
            rs= await cur.fetchmany(size)
        else:
            rs=await cur.fetchall()
        await cur.close()
        logging.info('rows returned: %s' %len(rs))
        return rs

class Model(dict, metaclass=ModelMetaclass):

    def __init__(self,**kw):
        super(Model, self).__init__(**kw)

class Field(object):
    def __init__(self, name, column_type, primary_key, default):
        self.name = name
        self.column_type = column_type
        self.primary_key = primary_key
        self.default = default
    def __str__(self):
        return '<%s, %s:%s>' % (self.__class__.__name__, self.column_type, self.name)
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
        table_name=attrs.get('__table__',None) or name
        logging.info('found table: %s (table: %s)'%(name,table_name))
        mappings=dict()
        fields=[]#field保存的是除主键外的属性名
        primarykey=None
        #k表示字段名
        for k,v in attrs.items():
            if isinstance(v,Field):
                logging.info('Found mapping %s==>%s' %(k,v))
                mappings[k]=v
                if v.primary_key:
                    logging.info('found primarykey')
                    if primarykey:
                        raise RuntimeError('Duplicated key for field')
                    primarykey=k
                else:
                    fields.append(k)
        if not primarykey:
            RuntimeError('primarykey not found')
        # w下面位字段从类属性中删除Field 属性
        #将类属性移除，使定义的类字段不污染User类属性，只在实例中可以访问这些key
        for k in mappings.keys():
            attrs.pop(k)



user=User(id=123,name='Michael')
user.insert()
users=User.findAll()
