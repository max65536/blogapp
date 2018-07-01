import logging; logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime
import orm
from coreweb import add_routes,add_static,get,add_route
from models import User,Blog
from aiohttp import web
from jinja2 import Environment,FileSystemLoader
from handlers import cookie2user,COOKIE_NAME

def init_jinja2(app,**kw):
    logging.info('init jinja2...')
    options = dict(
        autoescape = kw.get('autoescape', True),
        block_start_string = kw.get('block_start_string', '{%'),
        block_end_string = kw.get('block_end_string', '%}'),
        variable_start_string = kw.get('variable_start_string', '{{'),
        variable_end_string = kw.get('variable_end_string', '}}'),
        auto_reload = kw.get('auto_reload', True)
        )
    logging.info('kw=%s options=%s'%(str(kw),str(options)))
    path=kw.get('path',None)
    if path==None:
        path=os.path.join(os.path.dirname(os.path.abspath(__file__)),'templates')
    logging.info('set jinja2 template path:%s',path)
    env=Environment(loader=FileSystemLoader(path),**options)
    filters=kw.get('filters',None)
    if filters is not None:
        for name,f in filters.items():
            env.filters[name]=f
    app['__template__']=env

'''
factory大致结构:
async def foo_factory(app,handler):
    async foo(request):
        xxxxxx
        return (await handler(request))
    return foo
其实就是在handler(request)前加了预处理
'''

async def logger_factory(app,handler):
    #其实就是装饰器
    async def logger(request):
        #这里request参数是怎么传进去的?----修饰器
        # 记录日志:
        logging.info('Request: %s %s'%(request.method,request.path))
        # 继续处理请求:
        return(await handler(request))
    return logger

async def data_factory(app,handler):
    async def parse_data(request):
        logging.info('data_factory!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        logging.info('request.method:%s'%request.method)
        if request.method=='POST':
            logging.info('request.content_type: %s'% request.content_type)
            if request.content_type.startswith('application/json'):
                request.__data__=await request.json()
                logging.info('request json:%s '% str(request.__data__))
            elif request.content_type.startswith('application/x-www-form-urlencoded'):
                request.__data__=await request.post()
                logging.info('request form: %s '% str(request.__data__))
            elif request.content_type.startswith('image'):
                request.__data__=await request.post()
                logging.info('request image: %s '% str(request.__data__))
            elif request.content_type.startswith('multipart/form-data'):
                request.__data__=await request.post()
                logging.info('request multipart: %s '% str(request.__data__))
        return (await handler(request))
    return parse_data
'''
decorator里的代码是在装饰的时候就运行了，也就是@decorator的时候，也就是先与func运行*(此处func是handler)
原函数为handler(request)
'''
async def response_factory(app,handler):
    '''
    response这个middleware把返回值转换为web.Response对象再返回，以保证满足aiohttp的要求：
    '''
    async def response(request):
        logging.info('Response handler...')
        r=await handler(request)
        if isinstance(r,web.StreamResponse):
            return r
        if isinstance(r, bytes):
            resp=web.Response(body=r)
            resp.content_type='application/octet-stream'
        if isinstance(r, str):
            if r.startswith('rediect:'):
                return web.HTTPFound(r[9:])
            resp = web.Response(body=r.encode('utf-8'))
            resp.content_type = 'text/html;charset=utf-8'
            return resp
        if isinstance(r,dict):
            template=r.get('__template__')
            if template is None:
                resp=web.Response(body=json.dumps(r,ensure_ascii=False,default=lambda o:o.__dict__).encode('utf-8'))
                resp.content_type='application/json;charset=utf-8'
                return resp
            else:
                resp=web.Response(body=app['__template__'].get_template(template).render(**r).encode('utf-8'))
                resp.content_type='text/html;charset=utf-8'
                return resp
        if isinstance(r,int) and r>=100 and r<600:
            return web.Response(r)
        if isinstance(r,tuple) and len(r)==2:
            t,m=r
            if isinstance(t,int) and t>=100 and t<600:
                return web,Response(t,str(m))
        #default:
        resp=web.Response(body=str(r).encode('utf-8'))
        resp.content_type='text/plain;charset=utf-8'
        return resp
    return response
#问题？何处调用factory? 参见太阳尚远的博客！
async def auth_factory(app,handler):
    async def auth(request):
        logging.info('check user:%s %s'%(request.method,request.path))
        request.__user__=None
        cookie_str=request.cookies.get(COOKIE_NAME)
        if cookie_str:
            user=await cookie2user(cookie_str)
            if user:
                logging.info('set current user:%s'% user.email)
                request.__user__=user
        return (await handler(request))
    return auth

def datetime_filter(t):
    delta= int(time.time()-t)
    if delta < 60:
        return u'1分钟前'
    if delta < 3600:
        return u'%s分钟前' % (delta // 60)
    if delta < 86400:
        return u'%s小时前' % (delta // 3600)
    if delta < 604800:
        return u'%s天前' % (delta // 86400)
    dt=datetime.fromtimestamp(t)
    return u'%s年%s月%s日'%(dt.year,dt.month,dt.day)
# @get('/')
# async def index(request):
#     # u = User(id=2,name='Test4', email='tefasf@example.com', passwd='1234567890', image='about:blank')
#     # await u.save()
#     r=await User.findAll()
#     return{
#         '__template__':'test.html',
#         'users':r
#     }
    # logging.info('%s',r)
    # return web.Response(body=b'<h1>{{ r }}</h1>',content_type='text/html')
    # return web.Response('<body><h1>All users</h1>{% for u in users %}<p>{{ u.name }} / {{ u.email }}</p>{% endfor %}</body>',content_type='text/html')

@get('/')
async def index(request):
    summary='Lorem ipsum dolor sit amet, consectetur adipisicing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.'
    blogs=[
        Blog(id='1', name='Test Blog', summary=summary,created_at=time.time()-120),
        Blog(id='2',name='etw',summary=summary,created_at=time.time()-3600),
        Blog(id='3',name='what do you wany',summary=summary,created_at=time.time()-7200)
    ]
    return {
        '__template__':'blog.html',
        'blogs':blogs
    }

async def init(loop):
    # app=web.Application(loop=loop)
    # app.router.add_route('GET','/',index)
    # srv=await loop.create_server(app.make_handler(),'127.0.0.1',9000)
    # logging.info('server started at http://127.0.0.1:9000...')
    await orm.create_pool(loop=loop,host='localhost',port=3306,user='root',password='root',db='awesome')
    app=web.Application(loop=loop,middlewares=[logger_factory,auth_factory,data_factory,response_factory])#...

    # init_jinja2(app, filters=dict(datetime=datetime_filter))
    # add_routes(app, 'handlers')
    # add_static(app)
    # logging.info('#####################################')
    # logging.info(index.__dict__)
    init_jinja2(app,filters=dict(datetime=datetime_filter))
    # add_route(app,index)
    add_routes(app,'handlers')
    add_routes(app,'handlers_blog')
    add_static(app)
    # app.router.add_route('GET','/',index)
    srv = await loop.create_server(app.make_handler(),'127.0.0.1',9001)
    logging.info('server started at http://127.0.0.1:9001')

    return srv

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

