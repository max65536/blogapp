#!/usr/bin/python
# -*- coding: utf-8 -*-
import asyncio,os,inspect,logging,functools

from apis import APIError

from urllib import parse

from aiohttp import web
'''
eg:
@get('/blog/{id}')
def get_blog(id):
    pass
'''
def get(path):
    #define @get('/path')
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='GET'
        wrapper.__route__=path
        return wrapper
    # logging.info('#####################################')
    # logging.info(decorator.__dict__)
    return decorator

def post(path):
    #define @post('/path')
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kw):
            return func(*args,**kw)
        wrapper.__method__='POST'
        wrapper.__route__=path
        return wrapper
    return decorator

'''
def`foo(a, *b, c, **d):
    pass

a == POSITIONAL_OR_KEYWORD # a是用位置或参数名都可赋值的
b == VAR_POSITIONAL        # b是可变长列表
c == KEYWORD_ONLY          # c只能通过参数名的方式赋值
d == VAR_KEYWORD           # d是可变长字典

 POSITIONAL_ONLY 这类型在官方说明是不会出现在普通函数的，一般是内置函数什么的才会有，可能是self，cls或者是更底层的东西
'''
def get_required_kw_args(fn):
    args=[]
    params=inspect.signature(fn).parameters#返回fn的所有参数
    for name,param in params.items():
        #inspect.Parameter对象的default属性：如果这个参数有默认值，即返回这个默认值，如果没有，返回一个inspect._empty类。
        if param.kind==inspect.Parameter.KEYWORD_ONLY and param.default==inspect.Parameter.empty:
            args.append(name)
    return tuple(args)

def get_named_kw_args(fn):
    args=[]
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            args.append(name)

def has_named_kw_args(fn):
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.KEYWORD_ONLY:
            return True

def has_var_kw_arg(fn):
    params=inspect.signature(fn).parameters
    for name,param in params.items():
        if param.kind == inspect.Parameter.VAR_KEYWORD:
            return True

def has_request_arg(fn):
    '''
    如果找到request参数的话，后面还有POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD)这两类参数就报错，否则是不会报错的！
    '''
    sig=inspect.signature(fn)
    params=sig.parameters
    found=False
    for name,param in params.items():
        if name=='request':
            found=True
            continue
        if found and(param.kind!=inspect.Parameter.VAR_POSITIONAL and param.kind!=inspect.Parameter.KEYWORD_ONLY and param.kind!=inspect.Parameter.VAR_KEYWORD):
            raise ValueError('request parameter must be the last named parameter in function:%s%s'%(fn.__name__,str(sig)))
    return found

class RequestHandler(object):
    """
    URL处理函数不一定是一个coroutine，因此我们用RequestHandler()来封装一个URL处理函数。

    RequestHandler是一个类，由于定义了__call__()方法，因此可以将其实例视为函数。

    RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数，然后把结果转换为web.Response对象，这样，就完全符合aiohttp框架的要求
    #############################
    RequestHandler的主要作用就是构成标准的app.router.add_route第三个参数，还有就是获取不同的函数的对应的参数，就这两个主要作用。只要你实现了这个作用基本上是随你怎么写都行的
    #############################
    为什么要通过RequestHandler类来创建url处理函数，前面不是已经有url处理函数了吗？为什么不直接拿来用？
    答案就是我们要通过HTTP协议来判断在GET或者POST方法中是否丢失了参数，如果判断方法编写在url处理函数中会有很多重复代码，因此用类来封装一下
    """
    def __init__(self, app, fn):
        self._app = app
        #把func封装成coroutine
        self._func=fn
        self._has_request_arg= has_request_arg(fn)
        self._has_var_kw_arg=has_var_kw_arg(fn)
        self._has_named_kw_args=has_named_kw_args(fn)
        self._named_kw_args=get_named_kw_args(fn)
        self._required_kw_args=get_required_kw_args(fn)

    async def __call__(self,request):
        kw=None;
        # kw=request.xxx
        #待处理
        if self._has_var_kw_arg or self._has_named_kw_args or self._required_kw_args:
            if request.method=='POST':
                if not request.content_type:
                    return web.HTTPBadRequest('Miss content_type.')
                ct=request.content_type.lower()
                if ct.startswith('application/json'):
                    params=await request.json()
                    if not isinstance(params,dict):
                        return web.HTTPBadRequest('JSON body must be object.')
                    kw=params
                elif ct.startswith('application/x-www-form-urlencoded') or ct.startswith('multipart/form-data'):
                    params=await request.post()#???
                    kw=dict(**params)
                else:
                    return web.HTTPBadRequest('Unsupported content_type:%s'%request.content_type)
            if request.method=='GET':
                qs=request.query_string
                if qs:
                    kw=dict()
                    for k,v in parse.parse_qs(qs,True).items():
                        kw[k]=v[0]

        # logging.info('request.match_info')
        # logging.info(request.match_info)

        if kw is None:
            kw=dict(**request.match_info)
        else:
            if not self._has_var_kw_arg and self._named_kw_args:
                copy=dict()
                for name in self._named_kw_args:
                    if name in kw:
                        copy[name]=kw[name]
                kw=copy
            # check named arg:
            for k,v in request.match_info.items():
                if k in kw:
                    logging.warning('Dup;ocate arg named arg and kw args:%s'% k)
                kw[k]=v
        if self._has_request_arg:
            kw['request']=request
        #check required kw:
        if self._required_kw_args:
            for name in self._required_kw_args:
                if not name in kw:
                    logging.info('Missing argument: %s' % name)
                    return web.HTTPBadRequest('Missing argument: %s' % name)
        logging.info('call with args: %s'% str(kw))
        try:
            r = await self._func(**kw)
            return r
        except APIError as e:
            return dict(error=e.error, data=e.data, message=e.message)

def add_static(app):
    path1=os.path.join(os.path.dirname(os.path.abspath(__file__)),'static')
    # path2=os.path.join(os.path.dirname(os.path.abspath(__file__)),'blog_data')
    #用了aiohttp库的add_static()
    path2='../blog_data'
    app.router.add_static('/static/',path1)
    app.router.add_static('/image/',path2)
    logging.info('add static %s => %s'%('/static/',path1))
    logging.info('add image %s => %s'%('/image/',path2))

def add_route(app,fn):
    '''
    就是把fn通过aiohttp注册进app
    '''
    method=getattr(fn,'__method__',None)
    path=getattr(fn,'__route__',None)

    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn=asyncio.coroutine(fn)#包装成coroutine
        #inspect.signature（fn)将返回一个inspect.Signature类型的对象，值为fn这个函数的所有参数
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    # logging.info('%s %s %s'% (fn.__route__, fn.__method__, fn.__name__))
    app.router.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):
    n=module_name.rfind('.')
    if n==(-1):
        mod=__import__(module_name,globals(),locals())
    else:
        name=module_name[n+1:]
        mod=getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):#dir()返回模块的属性列表。
        if attr.startswith('_'):
            continue
        fn=getattr(mod,attr)
        if callable(fn):
            method=getattr(fn,'__method__',None)
            path=getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)
