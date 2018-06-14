
import asyncio,os,inspect,logging

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

class RequestHandler(object):
    """
    URL处理函数不一定是一个coroutine，因此我们用RequestHandler()来封装一个URL处理函数。

    RequestHandler是一个类，由于定义了__call__()方法，因此可以将其实例视为函数。

    RequestHandler目的就是从URL函数中分析其需要接收的参数，从request中获取必要的参数，调用URL函数，然后把结果转换为web.Response对象，这样，就完全符合aiohttp框架的要求
    """
    def __init__(self, app, fn):
        super(RequestHandler, self).__init__()
        self._app = app
        #把func封装成coroutine
        self._func=fn


    async def __call__(self,request):
        kw=0;
        # kw=request.xxx
        r=await self._func(**kw)
        return r

def add_route(app,fn):
    method=getattr(fn,'__method__',None)
    path=getattr(fn,'__route__',None)
    if path is None or method is None:
        raise ValueError('@get or @post not defined in %s.' % str(fn))
    if not asyncio.iscoroutinefunction(fn) and not inspect.isgeneratorfunction(fn):
        fn=asyncio.coroutine(fn)
    logging.info('add route %s %s => %s(%s)' % (method,path,fn.__name__,','.join(inspect.signature(fn).parameters.keys())))
    app.route.add_route(method,path,RequestHandler(app,fn))

def add_routes(app,module_name):
    n=module_name.rfind('.')
    if n==(-1):
        mod=__import__(module_name,globals(),locals())
    else:
        name=module_name[n+1:]
        mod=getattr(__import__(module_name[:n],globals(),locals(),[name]),name)
    for attr in dir(mod):
        if attr.startswith('_'):
            continue
        fn=getattr(mod,attr)
        if callable(fn):
            method=getattr(fn,'__method__',None)
            path=getattr(fn,'__route__',None)
            if method and path:
                add_route(app,fn)
