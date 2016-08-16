import datetime
from urllib.parse import unquote, urlparse, urlunparse
import uuid

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for)
from flask_security import (
    current_user,
    login_required,
    login_user,
    logout_user,
    roles_required)
from sqlalchemy import desc

from .forms import DetailsForm, SuitForm
from .models import Suit, User
from app.extensions import db, notify, oidc, pay, user_datastore


base = Blueprint('base', __name__)


def sanitize_url(url):

    if url:
        parts = list(urlparse(url))
        parts[0] = ''
        parts[1] = ''
        parts[3] = ''
        url = urlunparse(parts[:6])

    return url


@base.route('/login')
def login():
    "login redirects to Dex"

    next_url = sanitize_url(unquote(request.args.get('next', '')))
    if next_url:
        session['next_url'] = next_url

    return redirect(oidc.login('dex'))


@base.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('.index'))


@base.route('/oidc_callback')
@oidc.callback
def oidc_callback():
    user_info = oidc.authenticate('dex', request)

    user = user_datastore.get_user(user_info['email'])

    if not user:
        user = create_user(user_info)

    login_user(user)

    next_url = url_for('.details')

    if 'next_url' in session:
        next_url = session['next_url']
        del session['next_url']

    return redirect(next_url)


def create_user(user_info):
    email = user_info['email']

    user = add_role('USER', user_datastore.create_user(
        email=email))

    user_datastore.commit()

    return user


def add_role(role, user):
    user_role = user_datastore.find_or_create_role(role)
    user_datastore.add_role_to_user(user, user_role)
    return user


@base.route('/')
def index():
    print('index')

    suit = current_suit(current_user)
    if suit:
        return redirect(url_for('.status'))

    return render_template('index.html')


# @base.route('/login')
# @login_required
# def login():
    # "login redirects to OIDC provider"
    # return redirect(url_for('.details'))


@base.route('/details', methods=['GET', 'POST'])
@base.route('/details/<action>', methods=['GET', 'POST'])
@login_required
def details(action='set'):

    form = DetailsForm()

    user_name = getattr(current_user, 'name', None)

    if user_name:

        if action == 'set':
            suit = current_suit(current_user)

            if suit:
                return redirect(url_for('.status'))

            return redirect(url_for('.start_suit'))

    if form.validate_on_submit():
        current_user.update(**form.data)

        return redirect(url_for('.start_suit'))

    form.name.data = user_name
    form.email.data = getattr(current_user, 'email', '')
    form.mobile.data = getattr(current_user, 'mobile', '')

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

        return redirect(url_for('.make_payment'))

    return render_template('suit.html', form=form)


@base.route('/pay', methods=['GET', 'POST'])
@login_required
def make_payment():
    suit = current_suit(current_user)

    if request.method == 'POST':

        uid = str(uuid.uuid4())
        return_url = url_for('.confirm', _external=True, uid=uid)
        return_url = return_url.replace('http:', 'https:')

        description = (
            "I, {plaintiff}, wish to sue my brother, {defendant}, for his "
            "actions of which we will not speak, but which were despicable "
            "and wrong.").format(
                plaintiff=suit.plaintiff.name,
                defendant=suit.defendant.name)

        payment = pay.create_payment(100, description, return_url)

        session[uid] = payment.reference

        suit.update(payment=payment)

        return redirect(payment.next_url)

    return render_template('pay.html')


def current_suit(user):
    if user.is_authenticated:
        return Suit.query.filter(
            Suit.plaintiff == user).order_by(desc(Suit.created)).first()


@base.route('/confirm/<uid>')
@login_required
def confirm(uid):
    suit = current_suit(current_user)

    if uid not in session or session[uid] != suit.payment.reference:
        abort(404)

    pay.update_status(suit.payment)

    suit.update(confirmed=datetime.datetime.utcnow())

    notify['sms'].send_sms(
        suit.defendant.mobile,
        plaintiff=suit.plaintiff.name)

    flash('Payment successful. Lawsuit filed.')

    return redirect(url_for('.status'))


@base.route('/status')
@login_required
def status():
    suits = Suit.query.filter(Suit.confirmed.isnot(None)).all()
    return render_template('status.html', suits=suits)


@base.route('/admin')
@login_required
@roles_required('admin')
def admin():
    suits = Suit.query.all()
    return render_template('admin/index.html', suits=suits)


@base.route('/admin/suits/<suit>/accept', methods=['GET', 'POST'])
@login_required
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


@base.route('/admin/suits/<suit>/reject', methods=['POST'])
@login_required
@roles_required('admin')
def reject(suit):
    suit = Suit.query.get(suit)
    db.session.delete(suit)
    db.session.commit()
    flash('Suit rejected')
    return redirect(url_for('.admin'))


@base.route('/admin/users')
@login_required
@roles_required('admin')
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)


@base.route('/admin/users/<user>', methods=['POST'])
@login_required
@roles_required('admin')
def update_user(user):
    user = user_datastore.get_user(user)

    user.update(
        name=request.form['name'].strip(),
        email=request.form['email'].strip(),
        mobile=request.form['mobile'].strip(),
        active=bool(request.form['active'].strip())
    )

    admin_role = user_datastore.find_role('admin')

    make_admin = bool(request.form['admin'])
    if not user.has_role('admin'):

        if make_admin:
            user_datastore.add_role_to_user(user, admin_role)
            flash('Made {} an admin'.format(user.name))

    elif not make_admin:
        user_datastore.remove_role_from_user(user, admin_role)
        flash('Made {} not an admin'.format(user.name))

    db.session.commit()

    return redirect(url_for('.admin_users'))
