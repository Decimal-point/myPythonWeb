import logging;logging.basicConfig(level=logging.INFO) #设置调试级别，不设置就会pass
import aiomysql,asyncio


def log(sql,args=()):
    logging.info("SQL:%s"%sql) #打印sql语句

def pool(loop,**kw):
    logging.info("create sql pool..")
    global __pool
    __pool = yield from aiomysql.create_pool(
        host=kw.get("host",'localhost'),
        port=kw.get('port',3306),
        user=kw['user'],
        password=kw['password'],
        db=kw['db'],
        charset=kw.get('charset','utf8'),#utf8数据库编码
        autocommit=kw.get('autocommit',True),
        maxsize=kw.get('maxsize',10),
        minsize=kw.get('minsize',1),
        loop=loop
    )

@asyncio.coroutine
def select(sql,args,size=None):
    log(sql,args)
    with (yield from __pool) as conn:
        cursor = conn.cursor(aiomysql.DictCursor)
        yield from cursor.execute(sql.replace("?","%s"),args or())
        if size:
            rs = cursor.fecthmany(size)
        else:
            rs = cursor.fetchall()
        cursor.close()
        logging.info("rows returned:%d"%len(rs))
        return rs
@asyncio.coroutine
def execute(sql,args):
    log(sql,args)
    with (yield from __pool) as conn:
        try:
            cur = conn.cursor(aiomysql.DictCursor)
            cur.execute(sql.replace("?","%s"),args)
            count = cur.rowcount()
            cur.close
        except BaseException as e:
            raise
        return count