# -*- coding: utf-8 -*-
"""
Base models
"""

import datetime

from flask_security import RoleMixin, UserMixin

from app.extensions import db, pay
from lib.model_utils import GetOr404Mixin, GetOrCreateMixin, UpdateMixin
from lib.pay import PaymentMixin


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
    subject_id = db.Column(db.String(255), nullable=True)
    issuer_id = db.Column(db.String, nullable=True)
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
    payment_id = db.Column(db.String, db.ForeignKey('payment.reference'))
    payment = db.relationship(
        'Payment', backref='suit', foreign_keys=[payment_id], uselist=False)

    def save(self):
        db.session.add(self)
        db.session.commit()


@pay.payment_class
class Payment(db.Model, GetOrCreateMixin, UpdateMixin, PaymentMixin):
    reference = db.Column(db.String, primary_key=True)
    amount = db.Column(db.Integer)
    description = db.Column(db.String)
    url = db.Column(db.String, nullable=True)
    provider = db.Column(db.String, nullable=True)
    status = db.Column(db.String, nullable=True)
    finished = db.Column(db.Boolean, default=False)
    status_msg = db.Column(db.String, nullable=True)
    created = db.Column(db.DateTime, nullable=True)

    def __init__(self, *args, **kwargs):
        super(Payment, self).__init__(*args, **kwargs)
        self.next_url = None

    def save(self):
        db.session.add(self)
        db.session.commit()
