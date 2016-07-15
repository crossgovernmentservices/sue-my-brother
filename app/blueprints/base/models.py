# -*- coding: utf-8 -*-
"""
Base models
"""

import datetime

from flask_security import RoleMixin, UserMixin

from app.extensions import db
from lib.model_utils import GetOr404Mixin, GetOrCreateMixin, UpdateMixin


user_roles = db.Table(
    'user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id')))


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)
    description = db.Column(db.String(255))


class User(db.Model, UserMixin, GetOrCreateMixin, GetOr404Mixin, UpdateMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), nullable=True, unique=True)
    password = db.Column(db.String(255))
    mobile = db.Column(db.String(30), nullable=True)
    name = db.Column(db.String)
    active = db.Column(db.Boolean)
    confirmed_at = db.Column(db.DateTime)
    roles = db.relationship(
        'Role',
        secondary=user_roles,
        backref=db.backref('users', lazy='dynamic'))


class Suit(db.Model, GetOrCreateMixin, GetOr404Mixin, UpdateMixin):
    id = db.Column(db.Integer, primary_key=True)
    plaintiff_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    plaintiff = db.relationship(
        'User', backref='suits_brought', foreign_keys=[plaintiff_id])
    defendant_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    defendant = db.relationship(
        'User', backref='suits_against', foreign_keys=[defendant_id])
    created = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    confirmed = db.Column(db.DateTime, nullable=True)
    accepted = db.Column(db.DateTime, nullable=True)
    payment_id = db.Column(db.String, nullable=True)

    def save(self):
        db.session.add(self)
        db.session.commit()
