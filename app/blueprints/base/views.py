import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_security import current_user, login_required, roles_required
from sqlalchemy import desc

from .forms import DetailsForm, SuitForm
from .models import Suit, User
from app.extensions import db, notify


base = Blueprint('base', __name__)


@base.route('/')
def index():

    suit = current_suit(current_user)
    if suit:
        return redirect(url_for('.status'))

    return render_template('index.html')


@base.route('/details', methods=['GET', 'POST'])
@base.route('/details/<action>', methods=['GET', 'POST'])
@login_required
def details(action='set'):

    if current_user.name and action == 'set':

        suit = current_suit(current_user)
        if suit:
            return redirect(url_for('.status'))

        return redirect(url_for('.start_suit'))

    form = DetailsForm()

    if current_user.name:
        form.name.data = current_user.name
        form.email.data = current_user.email or ''
        form.mobile.data = current_user.mobile or ''

    if form.validate_on_submit():
        current_user.update(**form.data)

        return redirect(url_for('.start_suit'))

    return render_template('details.html', form=form)


@base.route('/start')
@login_required
def start():

    suit = current_suit(current_user)
    if suit:
        return redirect(url_for('.status'))

    return redirect(url_for('.start_suit'))


@base.route('/start-suit', methods=['GET', 'POST'])
@login_required
def start_suit():

    form = SuitForm()

    if form.validate_on_submit():
        brother, _ = User.get_or_create(name=form.brothers_name.data)

        if form.brothers_mobile.data:
            brother.update(mobile=form.brothers_mobile.data)

        suit = Suit(plaintiff=current_user, defendant=brother)
        suit.save()

        return redirect(url_for('.confirm'))

    return render_template('suit.html', form=form)


@base.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():

    if request.method == 'POST':
        flash('Payment successful, lawsuit filed')
        return redirect(url_for('.status'))

    return render_template('pay.html')


def current_suit(user):
    return Suit.query.filter(
        Suit.plaintiff == user).order_by(desc(Suit.created)).first()


@base.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm():
    suit = current_suit(current_user)

    if request.method == 'POST':
        suit.update(confirmed=datetime.datetime.utcnow())

        notify['sms'].send_sms(
            suit.defendant.mobile,
            plaintiff=suit.plaintiff.name)

        return redirect(url_for('.pay'))

    return render_template('confirm.html', suit=suit)


@base.route('/status')
@login_required
def status():
    suits = Suit.query.filter(Suit.confirmed.isnot(None)).all()
    return render_template('status.html', suits=suits)


@base.route('/admin')
@roles_required('admin')
def admin():
    suits = Suit.query.all()
    return render_template('admin/index.html', suits=suits)


@base.route('/admin/<suit>/accept', methods=['GET', 'POST'])
@roles_required('admin')
def accept(suit):
    suit = Suit.query.get(suit)
    suit.accepted = datetime.datetime.utcnow()
    db.session.add(suit)
    db.session.commit()

    notify['accept'].send_email(
        suit.plaintiff.email,
        plaintiff=suit.plaintiff.name,
        defendant=suit.defendant.name)

    flash('Suit accepted')
    return redirect(url_for('.admin'))


@base.route('/admin/<suit>/reject', methods=['POST'])
@roles_required('admin')
def reject(suit):
    suit = Suit.query.get(suit)
    db.session.delete(suit)
    db.session.commit()
    flash('Suit rejected')
    return redirect(url_for('.admin'))
