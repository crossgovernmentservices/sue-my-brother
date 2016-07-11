# -*- coding: utf-8 -*-
"""
Sue My Brother app factory class
"""

from lib.skeleton import AppFactory, context_processor


class SueMyBrother(AppFactory):

    from app.blueprints.base.views import base

    from app.extensions import db

    @context_processor
    def base_context_processor():
        return {'asset_path': '/static/govuk_template/assets/'}

    @classmethod
    def register_extensions(cls, app):
        super(SueMyBrother, cls).register_extensions(app)

        from app.assets import env
        env.init_app(app)

        from flask_migrate import Migrate
        migrate = Migrate()
        with app.app_context():
            migrate.init_app(app, cls.db)

        from flask_security import Security
        from app.extensions import user_datastore
        from app.blueprints.base.models import Role, User
        user_datastore.role_model = Role
        user_datastore.user_model = User
        Security(app, user_datastore)
