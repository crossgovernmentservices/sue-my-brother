from flask import Blueprint

from .permissions import setup_permissions


main = Blueprint('main', __name__)
main.record(setup_permissions)


from app.main.views import (  # noqa
    accept,
    admin,
    admin_suits,
    admin_users,
    confirm,
    delete_user,
    details,
    index,
    login,
    logout,
    make_payment,
    reauthenticate,
    reject,
    start,
    start_suit,
    status,
    update_user,
)
