import orm
async def main(loop):
    await create_pool(loop, **database)
    user = User()
    user.id = 1
    user.name = 'ZhouXiaorui_miao'
    await user.save()
    return user.name

loop = asyncio.get_event_loop()
database = {
    'host':'172.24.0.2', #数据库的地址
    'user':'root',
    'password':'123456',
    'db':'python_test'
}

task = asyncio.ensure_future(main(loop))

res = loop.run_until_complete(task)
print(res)
