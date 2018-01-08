from webApp.static.bean import  User
from webApp.static.coreWebService import get,post
import asyncio

@get("/")
def index(request):
    user = yield from User.findAll()
    return {
        '__template__':'test.html',
        'user':user
    }
