Traceback (most recent call last):
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/connection.py", line 464, in _connect
    await self._request_authentication()
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/connection.py", line 719, in _request_authentication
    auth_packet = await self._read_packet()
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/connection.py", line 554, in _read_packet
    packet.check_error()
  File "/usr/local/python3/lib/python3.6/site-packages/pymysql/connections.py", line 384, in check_error
    err.raise_mysql_exception(self._data)
  File "/usr/local/python3/lib/python3.6/site-packages/pymysql/err.py", line 107, in raise_mysql_exception
    raise errorclass(errno, errval)
pymysql.err.OperationalError: (1045, "Access denied for user 'root'@'localhost' (using password: YES)")

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "app.py", line 196, in <module>
    loop.run_until_complete(init(loop))
  File "/usr/local/python3/lib/python3.6/asyncio/base_events.py", line 467, in run_until_complete
    return future.result()
  File "app.py", line 176, in init
    await orm.create_pool(loop=loop,host='localhost',port=3306,user='root',password='Blog2018',db='awesome')
  File "/home/blogadmin/blogapp/www-18-07-05_04.32.06/orm.py", line 23, in create_pool
    loop=loop
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/pool.py", line 29, in _create_pool
    await pool._fill_free_pool(False)
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/pool.py", line 168, in _fill_free_pool
    **self._conn_kwargs)
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/connection.py", line 76, in _connect
    await conn._connect()
  File "/usr/local/python3/lib/python3.6/site-packages/aiomysql/connection.py", line 484, in _connect
    self._host) from e
pymysql.err.OperationalError: (2003, "Can't connect to MySQL server on 'localhost'")
