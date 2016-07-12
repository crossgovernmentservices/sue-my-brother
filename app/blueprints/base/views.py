from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import current_user
from flask_security import login_required
from sqlalchemy import desc

from .forms import DetailsForm, SuitForm
from .models import Suit, User


base = Blueprint('base', __name__)


@base.route('/')
def index():
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
        suit = Suit(plaintiff=current_user, defendant=brother)
        suit.save()

        return redirect(url_for('.pay'))

    return render_template('suit.html', form=form)


@base.route('/pay', methods=['GET', 'POST'])
@login_required
def pay():
    return render_template('pay.html')


def current_suit(user):
    return Suit.query.filter(
        Suit.plaintiff == user).order_by(desc(Suit.created)).first()


@base.route('/confirm', methods=['GET', 'POST'])
@login_required
def confirm():
    suit = current_suit(current_user)

    if request.method == 'POST':
        return redirect(url_for('.status'))

    return render_template('confirm.html', suit=suit)


@base.route('/status')
@login_required
def status():
    suit = current_suit(current_user)

    return render_template('status.html', suit=suit)
