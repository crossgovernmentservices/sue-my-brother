# -*- coding: utf-8 -*-
"""
Flask extensions instances, for access outside app.factory
"""

from flask_security import SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData, event
from sqlalchemy.engine import Engine
from sqlite3 import Connection as SQLite3Connection

from lib.notify import Notify
from lib.oidc_old import OIDC
from lib.pay import Pay


@event.listens_for(Engine, 'connect')
def set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, SQLite3Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute('PRAGMA foreign_keys=ON')
        cursor.close()


# XXX fixes SQLite unnamed constraints causing problems with migrations
naming_convention = {
    'ix': 'ix_%(column_0_label)s',
    'uq': 'uq_%(table_name)s_%(column_0_name)s',
    'ck': 'ck_%(table_name)s_%(column_0_name)s',
    'fk': 'fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s',
    'pk': 'pk_%(table_name)s'}
db = SQLAlchemy(metadata=MetaData(naming_convention=naming_convention))

notify = Notify()

user_datastore = SQLAlchemyUserDatastore(db, None, None)

oidc = OIDC()

pay = Pay()
