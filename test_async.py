
from apis import Page
import orm,asyncio,logging
from models import Blog
import time

async def init(loop):
    await orm.create_pool(loop=loop,host='localhost',port=3306,user='root',password='root',db='awesome')
    print('server started')
    await test_model()

async def test_dict(num=3,page_index=1):
    p=Page(num,page_index)
    print('p=',p)
    if num==0:
        return dict(page=p,blogs=())
    blogs= await Blog.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    x=dict(page=p,blogs=blogs)
    print('x=:',x)
    return x

async def test_select():
    num=await Blog.findNumber('count(id)')
    print(num)

async def test_model():
    print(Blog.__update__)
    print(Blog.__insert__)
    summary='fffffuufjk'
    blog=Blog(id='3',name='what do you wany',summary=summary,created_at=time.time()-7200)
    # print(blog.getValue)
    # print(blog.__fields__)
    # print('map=',list(map(blog.getValue,blog.__fields__)))
    blog.update()

loop=asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()

