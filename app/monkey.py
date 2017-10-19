from sqlalchemy import types
from sqlalchemy.ext.compiler import compiles


@compiles(types.DateTime, 'postgresql')
def pg_datetime(element, compiler, **kw):
    """
    去掉 PostgreSQL 中 TIMESTAMP 秒的小数部分
    """
    return 'TIMESTAMP(0)'


def do_patch():
    pass
