import re,time,json,logging,asyncio,hashlib,base64

from coreweb import get,post

from models import User,Blog,Comment,next_id

from apis import APIError,APIValueError

from aiohttp import web

from config import configs

_RE_EMAIL = re.compile(r'^[a-z0-9\.\-\_]+\@[a-z0-9\-\_]+(\.[a-z0-9\-\_]+){1,4}$')
_RE_SHA1 = re.compile(r'^[0-9a-f]{40}$')
COOKIE_NAME = 'awesession'
_COOKIE_KEY = configs.session.secret

def user2cookie(user,max_age):
    '''
    build cookie string by: id-expires-sha1
    "用户id" + "过期时间" + SHA1("用户id" + "用户口令" + "过期时间" + "SecretKey")
    '''
    expires=str(int(time.time()+max_age))
    s='%s-%s-%s-%s'%(user.id,user.passwd,expires,_COOKIE_KEY)
    L=[user.id,expires,hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    '''
    Parse cookie and load user if cookie is valid.
    '''
    if not cookie_str:
        return None
    try:
        L=cookie_str.split('-')
        if len(L)!=3:
            return None
        uid,expires,sha1=L
        if int(expires)<time.time():
            return None
        user=await User.find(uid)
        if user is None:
            return None
        s='%s-%s-%s-%s'%(uid,user.passwd,expires,_COOKIE_KEY)
        if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
            logging.info('invalid sha1')
            return None
        user.passwd='******'
        return user
    except Exception as e:
        logging.exception(e)
        raise None

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

@get('/register')
async def register():
    return{
        '__template__':'register.html'
    }

@get('/login')
async def login():
    return{
        '__template__':'login.html'
    }


@get('/api/users')
async def api_get_users():
    '''
    只要返回一个dict，后续的response这个middleware就可以把结果序列化为JSON并返回。
    '''
    users= await User.findAll()
    for u in users:
        u.passwd='*******'
    return dict(users=users)

@post('/api/users')
async def api_register_user(*,email,name,passwd):# *后面的参数被视为命名关键字参数
    if not name or not name.strip():
        #去除首尾空格
        raise APIValueError('name')
    if not email or not _RE_EMAIL.match(email):
        raise APIValueError('email')
    # if not passwd :
    if not passwd or not _RE_SHA1.match(passwd):
        raise APIValueError('passwd')
    users= await User.findAll('email=?',[email])#??????
    if len(users)>0:
        raise APIError('register:failed','email','Email is already registered')
    uid=next_id()
    sha1_passwd='%s:%s'%(uid,passwd)#注意用户口令是客户端传递的经过SHA1计算后的40位Hash字符串，所以服务器端并不知道用户的原始口令。
    user=User(id=uid,name=name.strip(),email=email,passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(),image='http://www.gravatar.com/avatar/%s?d=mm&s=120'% hashlib.md5(email.encode('utf-8')).hexdigest())
    await user.save()
    #make cookie
    r=web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body=json.dumps(user,ensure_ascii=False).encode('utf-8')
    return r

@post('/api/authenticate')
async def authenticate(*,email,passwd):
    if not email:
        raise APIValueError('email','invalid email.')
    if not passwd:
        raise APIValueError('passwd','invalid password.')
    #find user by email
    users=await User.findAll('email=?',[email])
    if len(users)==0:
        raise APIValueError('email','Email not exist.')
    user=users[0]

    #check password
    sha1=hashlib.sha1()
    sha1.update(user.id.encode('utf-8'))#如果数据量很大，可以分块多次调用update()
    sha1.update(b':')#???为何不是u':'
    sha1.update(passwd.encode('utf-8'))
    if user.passwd!= sha1.hexdigest():
        raise APIValueError('passwd','invalid password.')
    r=web.Response()
    r.set_cookie(COOKIE_NAME,user2cookie(user,86400),max_age=86400,httponly=True)
    user.passwd='******'
    r.content_type='application/json'
    r.body=json.dumps(user,ensure_ascii=False).encode('utf-8')#object2json
    return r

@post('/api/blogs')
async def api_create_blog(request,*,name,summary,content):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog=Blog(user_id=request.__user__.id,user_name=request.__user__.name,user_image=request.__user__.image,name=name.strip(),content=content.strip())
    await blog.save()
    return blog
