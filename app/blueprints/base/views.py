import datetime
import time
from urllib.parse import unquote, urlparse, urlunparse
import uuid
import humanize

from flask import (
    Blueprint,
    abort,
    after_this_request,
    current_app,
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
from .permissions import (
    accept_suit_permission,
    make_admin_permission,
    setup_permissions)
from app.extensions import db, notify, oidc, pay, user_datastore


base = Blueprint('base', __name__)
base.record(setup_permissions)


def get_current_user():
    user = current_user

    if not user.is_authenticated:
        if 'user' in session and session['user']:
            user.update(**session['user'])

    return user


def set_current_user(user):
    if user and not user.is_authenticated:
        session['user'] = {
            'email': user.email,
            'mobile': user.mobile,
            'name': user.name}


def sanitize_url(url):

    if url:
        parts = list(urlparse(url))
        parts[0] = ''
        parts[1] = ''
        parts[3] = ''
        url = urlunparse(parts[:6])

    return url


def authenticated_within(max_age):
    auth_time = session["iat"]
    time_elapsed_since_authenticated = int(time.time()) - auth_time

    return time_elapsed_since_authenticated <= max_age


def force_authentication(path=None):
    session["next_url"] = path or url_for('base.index')
    return redirect(oidc.login(force_reauthentication=True))


@base.route('/set_idp', methods=['GET', 'POST'])
def set_idp():
    idp = request.form["idp"]
    caller = request.args.get('caller', url_for('base.index'))

    after_this_request(oidc.set_current_provider(idp))

    return redirect(caller)


@base.route('/reauthenticate/')
def reauthenticate():
    return force_authentication(request.args.get('caller', None))


@base.route('/login')
def login():
    "login redirects to currently selected OIDC provider"

    next_url = sanitize_url(unquote(request.args.get('next', '')))
    if next_url:
        session['next_url'] = next_url

    return redirect(oidc.login())


@base.route('/logout')
def logout():
    logout_user()
    set_current_user(current_user)
    return redirect(url_for('.index'))


@base.route('/oidc_callback')
@oidc.callback
def oidc_callback():
    user_info = oidc.authenticate()

    session["iat"] = user_info["iat"]

    user = user_datastore.get_user(user_info.get(
        'email', user_info.get('upn')))

    if not user:
        user = create_user(user_info)

    user_name = getattr(user, 'name')
    if user_name is None:
        user_name = user_info.get('name')
        user.name = user_name
        db.session.commit()

    login_user(user)

    next_url = url_for('.details')

    if 'next_url' in session:
        next_url = session['next_url']
        if next_url == 'admin/users':
            session["reauthenticated"] = True

        del session['next_url']

    return redirect(next_url)


def create_user(user_info):
    email = user_info.get('email', user_info.get('upn'))

    user = add_role('USER', user_datastore.create_user(
        email=email,
        issuer_id=user_info["iss"],
        subject_id=user_info["sub"]))

    user_datastore.commit()

    return user


def add_role(role, user):
    user_role = user_datastore.find_or_create_role(role)
    user_datastore.add_role_to_user(user, user_role)
    return user


def current_suit(user):
    return Suit.query.join(User, Suit.plaintiff_id == User.id).filter(
        User.email == user.email
    ).order_by(desc(Suit.created)).first()


@base.route('/')
def index():
    suit = current_suit(get_current_user())
    if suit:
        return redirect(url_for('.status', suit=suit.id))

    return render_template('index.html')


@base.route('/details', methods=['GET', 'POST'])
@base.route('/details/<action>', methods=['GET', 'POST'])
def details(action='set'):

    form = DetailsForm()

    user = get_current_user()
    user_name = getattr(user, 'name', None)

    if user_name:

        if action == 'set':
            suit = current_suit(user)

            if suit:
                return redirect(url_for('.status', suit=suit.id))

            return redirect(url_for('.start_suit'))

    if form.validate_on_submit():
        user.update(**form.data)
        set_current_user(user)

        return redirect(url_for('.start_suit'))

    form.name.data = user_name
    form.email.data = getattr(user, 'email', '')
    form.mobile.data = getattr(user, 'mobile', '')

    return render_template('details.html', form=form)


@base.route('/start')
def start():

    suit = current_suit(get_current_user())
    if suit:
        return redirect(url_for('.status', suit=suit.id))

    return redirect(url_for('.start_suit'))


@base.route('/start-suit', methods=['GET', 'POST'])
def start_suit():

    form = SuitForm()

    user = get_current_user()

    if form.validate_on_submit():
        plaintiff, _ = User.get_or_create(email=user.email)
        if user.name:
            plaintiff.name = user.name
        brother, _ = User.get_or_create(name=form.brothers_name.data)

        if form.brothers_mobile.data:
            brother.update(mobile=form.brothers_mobile.data)

        suit = Suit(plaintiff=plaintiff, defendant=brother)
        suit.save()

        return redirect(url_for('.make_payment'))

    return render_template('suit.html', form=form)


@base.route('/pay', methods=['GET', 'POST'])
def make_payment():
    suit = current_suit(get_current_user())

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


@base.route('/confirm/<uid>')
def confirm(uid):
    suit = current_suit(get_current_user())

    if uid not in session or session[uid] != suit.payment.reference:
        abort(404)

    pay.update_status(suit.payment)

    suit.update(confirmed=datetime.datetime.utcnow())

    if suit.defendant.mobile:
        notify['sms'].send_sms(
            suit.defendant.mobile,
            plaintiff=suit.plaintiff.name)

    flash('Payment successful. Lawsuit filed.')

    return redirect(url_for('.status', suit=suit.id))


@base.route('/status/<suit>')
def status(suit):
    suit = Suit.get_or_404(id=suit)
    return render_template('status.html', suit=suit)


@base.app_template_filter("prettydate")
def pretty_date(date):
    return humanize.naturaltime(
        datetime.datetime.now() - datetime.datetime.fromtimestamp(date))


@base.route('/admin')
@login_required
@roles_required('admin')
def admin():
    return render_template('admin/index.html')


@base.route('/admin/suits')
@login_required
@roles_required('admin')
def admin_suits():
    suits = Suit.query.all()
    return render_template(
        'admin/suits.html',
        suits=suits,
        can_accept_suit=accept_suit_permission.can())


@base.route('/admin/suits/<suit>/accept', methods=['GET', 'POST'])
@login_required
@roles_required('admin')
@accept_suit_permission.require()
def accept(suit):
    suit_obj = Suit.query.get(suit)

    max_age = current_app.config.get("ACCEPT_SUIT_MAX_AGE")
    if not authenticated_within(max_age):
        return force_authentication()

    suit_obj.accepted = datetime.datetime.utcnow()
    db.session.add(suit_obj)
    db.session.commit()

    notify['accept'].send_email(
        suit_obj.plaintiff.email,
        plaintiff=suit_obj.plaintiff.name,
        defendant=suit_obj.defendant.name)

    flash('Suit accepted')
    return redirect(url_for('.admin'))


@base.route('/admin/suits/<suit>/reject', methods=['POST'])
@login_required
@roles_required('admin')
@accept_suit_permission.require()
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
    if not session.pop("reauthenticated", None):
        return reauthenticate('admin/users')

    users = User.query.all()
    return render_template(
        'admin/users.html',
        users=users,
        can_make_admin=make_admin_permission.can())


@base.route('/admin/users/<user>', methods=['POST'])
@login_required
@roles_required('admin')
def update_user(user):
    user = user_datastore.get_user(user)

    if request.form['name']:
        user.name = request.form['name'].strip()

    if request.form['email']:
        user.email = request.form['email'].strip()

    if request.form['mobile']:
        user.mobile = request.form['mobile'].strip()

    admin_role = user_datastore.find_role('admin')

    with make_admin_permission.require():
        user.is_superadmin = bool(request.form['superadmin'])
        user.can_accept_suits = bool(request.form['accept_suits'])

        if 'admin' in request.form:
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


@base.route('/admin/users/<user>/delete', methods=['POST'])
@login_required
@roles_required('admin')
def delete_user(user):
    user_id = user
    user = user_datastore.get_user(user)

    with make_admin_permission.require():
        user_datastore.delete_user(user)
        flash('Deleted user #{}'.format(user_id))

    db.session.commit()

    return redirect(url_for('.admin_users'))
