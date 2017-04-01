import time
from datetime import datetime, date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.types import String

from config import config

_db_url = 'postgresql+psycopg2://{user}:{password}@{host}/{db}'.format(**config.db_info)

engine = create_engine(_db_url, echo=config.db_echo)
Base = declarative_base(bind=engine)
Session = sessionmaker(bind=engine)


class AlchemyMixin(object):
    def __setattr__(self, key, value):
        # 当给 String 类型字段赋值时限制字符串的长度, 如 Column(String(20)) 中最长只能有 20 个字符.
        if isinstance(value, str):
            the_attribute = getattr(self.__class__, key, None)

            if isinstance(the_attribute, InstrumentedAttribute):
                # is a column
                if isinstance(the_attribute.property.columns[0].type, String):
                    max_length = the_attribute.property.columns[0].type.length
                    value = value[:max_length]

        super().__setattr__(key, value)

    @classmethod
    def get(cls, object_id, session):
        """
        Get object by object id, if not find, return None.
        """
        the_object = session.query(cls).filter(
            cls.id == object_id
        ).first()

        return the_object

    def to_dict(self, **kwargs):
        """
        将一个 SQLAlchemy 的对象 (row, declarative_base) 转为 dict.
        如果 kwargs 有 columns, 则 columns 是所有需要的项; 若有 excluded, 则 excluded 是要排除的项. 二者不可并存.
        """
        d = {}

        columns = kwargs.get('columns')

        if columns:
            columns = [x.key for x in columns]

        else:
            # 不需要的项
            excluded = kwargs.get('excluded')
            columns = set(x.name for x in self.__table__.columns)

            if excluded:
                excluded = set(x.key for x in excluded)
                columns -= excluded

        for column in columns:
            value = getattr(self, column)

            if isinstance(value, datetime):
                value = int(time.mktime(value.timetuple()))
            elif isinstance(value, date):
                value = value.isoformat()
            elif isinstance(value, Decimal):
                value = str(value)

            d[column] = value

        return d


def print_create_table_sql(model):
    """
    打印下数据表的创建语句, 以便手动创建等...
    """
    # from sqlalchemy.schema import CreateTable

    # print('#### Create table SQL for model {}: ####'.format(model))
    # print(CreateTable(model.__table__).compile(engine))
    # print('#' * 20)


def create_table_if_not_exist(the_object):
    """
    如果需要的表不存在, 创建它
    """
    # the_object.__table__.create(engine, checkfirst=True)
