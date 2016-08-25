from flask_security import current_user
from flask_principal import Need, Permission, identity_loaded


accept_suit_need = Need('accept_suit', True)
accept_suit_permission = Permission(accept_suit_need)

make_admin_need = Need('make_admin', True)
make_admin_permission = Permission(make_admin_need)


def grant_permissions(sender, identity):
    if hasattr(current_user, 'is_superadmin'):
        if current_user.is_superadmin:
            identity.provides.add(make_admin_need)
    if hasattr(current_user, 'can_accept_suits'):
        if current_user.can_accept_suits:
            identity.provides.add(accept_suit_need)


def setup_permissions(state):
    identity_loaded.connect_via(state.app)(grant_permissions)
