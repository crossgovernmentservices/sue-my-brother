# -*- coding: utf-8 -*-
"""
Sue My Brother forms
"""

from flask_wtf import Form
from wtforms import StringField
from wtforms.validators import DataRequired


class DetailsForm(Form):
    name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email Address')
    mobile = StringField('Mobile Phone Number')


class SuitForm(Form):
    brothers_name = StringField('Your Brother\'s Full Name', validators=[DataRequired()])
    brothers_mobile = StringField('Your Brother\'s Mobile Phone Number')
