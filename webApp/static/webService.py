import logging;logging.basicConfig(level=logging.INFO)
import asyncio,os,json,time
from datetime import datetime

from aiohttp import web

def index(request):
   return web.Response(body=b'<h1>come!</h1>',content_type='text/html')

@asyncio.coroutine
def init(loop):
    app = web.Application(loop=loop)
    app.router.add_route('GET','/',index)
    server = yield from loop.create_server(app.make_handler(),"127.0.0.1",9001)
    logging.info("server starts in http://127.0.0.1:9001")
    return server

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()