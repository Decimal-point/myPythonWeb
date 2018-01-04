import logging;logging.basicConfig(level=logging.INFO)
import webApp.static.sqlService

class Field(object):
    def __init__(self,name,type,primary_key,default):
        self.name = name #列名
        self.type = type #数据类型
        self.primary_key = primary_key #是否是主键
        self.default = default #默认值

    def __str__(self):
        return '<%s,%s:%s>'%(self.__class__.__name__,self.type,self.name)

class StringField(Field):
    def __init__(self,name = None,primary_key = False,default = None,type = "varchar(100)"):
        Field.__init__(self,name,type,primary_key,default)
class IntegerField(Field):
    def __init__(self,name = None,primary_key = False,default = 0,type = "int"):
        Field.__init__(self,name,type,primary_key,default)
class BooleanField(Field):
    def __init__(self,name = None,primary_key = False,default = False,type = "boolean"):
        Field.__init__(self,name,type,primary_key,default)
class FloatField(Field):
    def __init__(self,name = None,primary_key = False,default = 0.0,type = "real"):
        Field.__init__(self,name,type,primary_key,default)

class ModelMetaclass(type):
    def __new__(cls, name, bases, attrs):
        # 排除Model类本身:
        if name=='Model':
            return type.__new__(cls, name, bases, attrs)
        # 获取table名称:
        tableName = attrs.get('__table__', None) or name
        logging.info('found model: %s (table: %s)' % (name, tableName))
        # 获取所有的Field和主键名:
        mappings = dict()
        fields = []
        primaryKey = None
        for k, v in attrs.items():
            if isinstance(v, Field):
                logging.info('  found mapping: %s ==> %s' % (k, v))
                mappings[k] = v
                if v.primary_key:
                    # 找到主键:
                    if primaryKey:
                        raise RuntimeError('Duplicate primary key for field: %s' % k)
                    primaryKey = k
                else:
                    fields.append(k)
        if not primaryKey:
            raise RuntimeError('Primary key not found.')
        for k in mappings.keys():
            attrs.pop(k)
        escaped_fields = list(map(lambda f: '`%s`' % f, fields))
        print(mappings)
        attrs['__mappings__'] = mappings # 保存属性和列的映射关系
        attrs['__table__'] = tableName
        attrs['__primary_key__'] = primaryKey # 主键属性名
        attrs['__fields__'] = fields # 除主键外的属性名
        # 构造默认的SELECT, INSERT, UPDATE和DELETE语句:
        attrs['__select__'] = 'select `%s`, %s from `%s`' % (primaryKey, ', '.join(escaped_fields), tableName)
        attrs['__insert__'] = 'insert into `%s` (%s, `%s`) values (%s)' % (tableName, ', '.join(escaped_fields), primaryKey, create_args_string(len(escaped_fields) + 1))
        attrs['__update__'] = 'update `%s` set %s where `%s`=?' % (tableName, ', '.join(map(lambda f: '`%s`=?' % (mappings.get(f).name or f), fields)), primaryKey)
        attrs['__delete__'] = 'delete from `%s` where `%s`=?' % (tableName, primaryKey)
        return type.__new__(cls, name, bases, attrs)

#创建拥有几个占位符的字符串
def create_args_string(num):
    L = []
    for n in range(num):
        L.append('?')
    return ', '.join(L)

class Model(dict, metaclass=ModelMetaclass):

    def __init__(self, **kw):
        super(Model, self).__init__(**kw)

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(r"'Model' object has no attribute '%s'" % key)

    def __setattr__(self, key, value):
        self[key] = value

    def getValue(self, key):
        return getattr(self, key, None)

    def getValueOrDefault(self, key):
        value = getattr(self, key, None)
        if value is None:
            field = self.__mappings__[key]
            if field.default is not None:
                value = field.default() if callable(field.default) else field.default
                logging.debug('using default value for %s: %s' % (key, str(value)))
                setattr(self, key, value)
        return value
    async def findAll(cls, where=None, args=None, **kw):
        ' find objects by where clause. '
        sql = [cls.__select__]
        if where:
            sql.append('where')
            sql.append(where)
        if args is None:
            args = []
        orderBy = kw.get('orderBy', None)
        if orderBy:
            sql.append('order by')
            sql.append(orderBy)
        limit = kw.get('limit', None)
        if limit is not None:
            sql.append('limit')
            if isinstance(limit, int):
                sql.append('?')
                args.append(limit)
            elif isinstance(limit, tuple) and len(limit) == 2:
                sql.append('?, ?')
                args.extend(limit)
            else:
                raise ValueError('Invalid limit value: %s' % str(limit))
        rs = webApp.static.sqlService.select(' '.join(sql), args)
        return [cls(**r) for r in rs]


    #该方法不了解
    @classmethod
    async def findNumber(cls, selectField, where=None, args=None):
        ' find number by select and where. '
        sql = ['select %s _num_ from `%s`' % (selectField, cls.__table__)]
        if where:
            sql.append('where')
            sql.append(where)
        rs = webApp.static.sqlService.select(' '.join(sql), args, 1)
        if len(rs) == 0:
            return None
        return rs[0]['_num_']


    #主键查找的方法
    @classmethod
    async def find(cls, pk):
        ' find object by primary key. '
        rs = webApp.static.sqlService.select('%s where `%s`=?' % (cls.__select__, cls.__primary_key__), [pk], 1)
        if len(rs) == 0:
            return None
        return cls(**rs[0])


    #一下的都是对象方法,所以可以不用传任何参数,方法内部可以使用该对象的所有属性,及其方便
    #保存实例到数据库
    async def save(self):
        print()
        args = list(map(self.getValueOrDefault, self.__fields__))
        args.append(self.getValueOrDefault(self.__primary_key__))
        rows =webApp.static.sqlService.execute(self.__insert__, args)
        if rows != 1:
            logging.info('failed to insert record: affected rows: %s' % rows)
    #更新数据库数据
    async def update(self):
        args = list(map(self.getValue, self.__fields__))
        args.append(self.getValue(self.__primary_key__))
        rows = webApp.static.sqlService.execute(self.__update__, args)
        if rows != 1:
            logging.info('failed to update by primary key: affected rows: %s' % rows)
    #删除数据
    async def remove(self):
        args = [self.getValue(self.__primary_key__)]
        rows = webApp.static.sqlService.execute(self.__delete__, args)
        if rows != 1:
            logging.info('failed to remove by primary key: affected rows: %s' % rows)
