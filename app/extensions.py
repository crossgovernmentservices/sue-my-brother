# -*- coding: utf-8 -*-
"""
Flask extensions instances, for access outside app.factory
"""

from flask_security import SQLAlchemyUserDatastore
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()

user_datastore = SQLAlchemyUserDatastore(db, None, None)
