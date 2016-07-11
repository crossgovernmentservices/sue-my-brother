from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user
from flask_security import login_required

from .forms import DetailsForm, SuitForm
from .models import Suit, User


base = Blueprint('base', __name__)


@base.route('/')
def index():
    return render_template('index.html')


@base.route('/start', methods=['GET', 'POST'])
@login_required
def start():
    form = DetailsForm()

    if form.validate_on_submit():
        current_user.update(**form.data)

        return redirect(url_for('.start_suit'))

    return render_template('start.html', form=form)


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
    return 'Pay'
