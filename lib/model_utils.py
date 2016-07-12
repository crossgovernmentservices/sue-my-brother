# -*- coding: utf-8 -*-
"""
Util mixins for models
"""

from flask import abort
from sqlalchemy.orm.exc import MultipleResultsFound, NoResultFound

from app.extensions import db


class GetOrCreateMixin(object):

    @classmethod
    def get_or_create(cls, **kwargs):
        try:
            return cls.query.filter_by(**kwargs).one(), False

        except NoResultFound:
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            return obj, True

        except MultipleResultsFound:
            raise


class GetOr404Mixin(object):

    @classmethod
    def get_or_404(cls, **kwargs):
        try:
            obj = cls.query.filter_by(**kwargs).one()

        except NoResultFound:
            abort(404)

        except MultipleResultsFound:
            raise

        return obj


class UpdateMixin(object):

    def update(self, **kwargs):
        for key, val in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, val)

        db.session.add(self)
        db.session.commit()
