import inspect

def add_routes(module_name):
    n=module_name.rfind('.')
    print(n)
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
                print(fn.__method__,fn.__route__,fn.__name__)

add_routes('handlers_blog')
