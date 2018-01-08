import time,webApp.static.sqlService,uuid
from webApp.static.ORMService import Model,StringField,IntegerField
import asyncio

def next_id():
    return '%015d%s000' % (int(time.time() * 1000), uuid.uuid4().hex)

class User(Model):
    __table__ = "user"
    u_id = IntegerField(primary_key=True)
    u_name = StringField(type="varchar(50)")
    u_sex = StringField(type="varchar(50)")
    u_phone = StringField(type="varchar(50)")


def test(loop):
    yield from webApp.static.sqlService.pool(loop=loop,user='root',password='tomtop',db='test')
    print("come")
    #u = User(u_name="tom",u_sex="M",u_phone="123456")
    #yield from u.save()
    u = yield from User.find(pk=10)
    print(u.u_id)





