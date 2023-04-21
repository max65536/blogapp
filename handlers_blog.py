#!/usr/bin/python
# -*- coding: utf-8 -*-
import re,time,json,logging,asyncio,hashlib,base64,os,shutil,random

import markdown,markdown2

from coreweb import get,post

from models import User,Blog,Comment,next_id

from apis import APIError,APIValueError,Page

from aiohttp import web

from config import configs

from handlers import get_page_index,check_admin

def time2dirname(timastamp):
    return time.strftime("%Y-%m-%d_%H-%M-%S", time.localtime(timastamp))

def moveAll(origin,destination):
    os.makedirs(destination,exist_ok=True)
    for file in os.listdir(origin):
        shutil.move('%s/%s'%(origin,file),destination)

def content_modified(content,dirname):
    return content.replace('./blog_images','/image/%s'%dirname)

@get('/')
async def index(*,page=1):
    dic=await api_list_blogs(page=page)
    blogs=dic['blogs']
    pageclass=dic['page']
    return {
        '__template__':'blogs.html',
        'page_index':get_page_index(page),
        'blogs':blogs,
        'page':pageclass
    }

#blog管理
@get('/manage')
def manage(request):
    if request.__user__ and request.__user__['email']=='max@163.com':
        r=web.HTTPFound('/manage/blogs')
        return r
    else:
        return '请用管理员账号登入'

@get('/manage/blogs')
def manage_blogs(*,page='1'):
    # logging.info('page=%s!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'%page)
    return {
        '__template__':'manage_blogs.html',
        'page_index':get_page_index(page)
    }

@get('/manage/blogs2')
def manage_blogs2(*,page='1'):
    return {
        '__template__':'manage_blogs2.html',
        'page_index':get_page_index(page)
    }

@get('/manage/blogs/create')
def manage_blogs_create():
    return{
        '__template__':'manage_blog_edit.html',
        'id':'',
        'action':'/api/blogs'
    }

@get('/manage/blogs/create2')
def manage_blogs_create2():
    return{
        '__template__':'manage_blog_edit2.html',
        'id':'',
        'action':'/api/blogs'
    }

@get('/manage/blogs/delete')
async def manage_blogs_delete(*,id):
    if not id:
        raise APIValueError('id', 'id cannot be empty.')
    await Blog.delete(id)

@get('/manage/blogs/edit')
async def manage_blogs_edit(*,id):
    return{
        '__template__':'manage_blog_edit.html',
        'id':id,
        'action':'/api/blogs/%s'%id
    }

#blog浏览
@get('/blogs')
async def get_blogs():
    blogs= await Blog.findAll(orderBy='created_at desc')
    # return dict(blogs=blogs)
    return {
        '__template__':'blogs.html',
        'blogs':blogs
    }

@get('/blog/{id}')
async def get_blog_details(id):
    blog=await Blog.find(id)
    blog.html_content=markdown.markdown(blog.content,extensions=[
                                     'markdown.extensions.extra',
                                     'markdown.extensions.codehilite',
                                     'markdown.extensions.toc',
                                    # 'mdx_math'
                                    ])
    imagelist=os.listdir('../blog_data/user')
    image='/image/user/%s'%random.sample(imagelist,1)[0]
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    return {
        '__template__':'blog_details.html',
        'blog':blog,
        'image':image,
        'comments':comments
    }
#blog的api
@get('/api/blogs')
async def api_blogs(*,page='1'):
    '''
    只要返回一个dict，后续的response这个middleware就可以把结果序列化为JSON并返回。
    '''
    blogs= await Blog.findAll()
    # return dict(blogs=blogs)
    return {
        '__template__':'blogs.html',
        'blogs':blogs
    }

@get('/api/list/blogs')
async def api_list_blogs(*,page='1'):
    page_index=get_page_index(page)
    num=await Blog.findNumber('count(id)')
    p=Page(num,page_index)
    if num==0:
        return dict(page=p,blogs=())
    blogs= await Blog.findAll(orderBy='created_at desc',limit=(p.offset,p.limit))
    return dict(page=p,blogs=blogs)


@get('/api/blogs/{id}')
async def api_get_blog(*,id):
    blog=await Blog.find(id)
    return blog


@post('/api/blogs')
async def api_create_blog(request,*,name,summary,content,image=''):
    check_admin(request)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog=Blog(user_id=request.__user__.id,user_name=request.__user__.name,user_image=request.__user__.image,name=name.strip(),summary=summary.strip(),content='',image=image)
    await blog.save()
    if image =='':
        blog.content=content.strip()
    else:
        dirname=time2dirname(blog.created_at)
        moveAll('../blog_data/temp','../blog_data/%s'%dirname)
        blog.content=content_modified(content.strip(),dirname)
        blog.image=image
    await blog.update()

    return blog

@post('/api/blogs/{id}')
async def api_update_blog(id,request,*,name,summary,content,image=''):
    check_admin(request)
    blog = await Blog.find(id)
    if not name or not name.strip():
        raise APIValueError('name', 'name cannot be empty.')
    if not summary or not summary.strip():
        raise APIValueError('summary', 'summary cannot be empty.')
    if not content or not content.strip():
        raise APIValueError('content', 'content cannot be empty.')
    blog.name = name.strip()
    blog.summary = summary.strip()
    logging.info('image=%s'%image)
    logging.info('blog.image=%s'%blog.image)
    if (blog.image=='') and (image==''):
        blog.content=content.strip()
    else:
        dirname=time2dirname(blog.created_at)
        moveAll('../blog_data/temp','../blog_data/%s'%dirname)
        blog.content = content_modified(content.strip(),dirname)
        blog.image=blog.image+image

    await blog.update()
    return blog

@post('/api/blogs/{id}/delete')
async def api_delete_blog(request, *, id):
    check_admin(request)
    blog = await Blog.find(id)
    shutil.rmtree('../blog_data/%s'%time2dirname(blog.created_at))
    await blog.remove()
    return dict(id=id)

@post('/api/upload/image')
async def store_pic(request):
    # 如果是个很大的文件不要用这种方法。
    logging.info('upload image....................................')
    # logging.info(request.__data__)
    if request.__data__ is None:
        return None
    file=request.__data__['files[]']
    if file is None:
        return None
    filename=file.filename
    file_content=file.file
    path='../blog_data/temp/%s'%filename
    new_file=open(path,'wb')
    for line in file_content:
        new_file.write(line)
    new_file.close()
    return {
        'path':path
        }

@get('/api/comments')
async def api_comments(*, page='1'):
    # page_index = get_page_index(page)
    # num = await Comment.findNumber('count(id)')
    # p = Page(num, page_index)
    # if num == 0:
    #     return dict(page=p, comments=())
    # comments = await Comment.findAll(orderBy='created_at desc', limit=(p.offset, p.limit))
    # return dict(page=p, comments=comments)
    comments = await Comment.findAll(orderBy='created_at desc')
    return comments

@post('/api/blogs/{id}/comments')
async def api_create_comment(id, request, *, name,content,image):
    # user = request.__user__
    # if user is None:
    #     raise APIPermissionError('Please signin first.')
    if not content or not content.strip():
        raise APIValueError('content')
    blog = await Blog.find(id)
    if blog is None:
        raise APIResourceNotFoundError('Blog')
    # imagelist=os.listdir('../blog_data/user')
    # image='../blog_data/user/%s'%random.sample(imagelist,1)[0]
    comment = Comment(blog_id=blog.id, user_name=name, user_image=image, content=content.strip())
    await comment.save()
    return comment
