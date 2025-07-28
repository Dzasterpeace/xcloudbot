from flask import Blueprint

from .auth import auth_bp
from .admin import admin_bp
from .systems import systems_bp
from .tips import tips_bp
from .bets import bets_bp
from .tipster_access import tipster_access_bp
from .tipster_control import tipster_control_bp
from .admin_tipster_access import admin_tipster_access_bp
from .automate import cron_bp
from .users import users_bp
from .betfair_oauth import oauth_bp

bp = Blueprint('api', __name__)

bp.register_blueprint(oauth_bp, url_prefix='/betfair')
bp.register_blueprint(auth_bp, url_prefix='/auth')
bp.register_blueprint(admin_bp, url_prefix='/admin')
bp.register_blueprint(systems_bp, url_prefix='/systems')
bp.register_blueprint(tips_bp, url_prefix='/tips')
bp.register_blueprint(bets_bp, url_prefix='/bets')
bp.register_blueprint(tipster_access_bp, url_prefix='/tipster-access')
bp.register_blueprint(tipster_control_bp, url_prefix='/tipster-control')
bp.register_blueprint(admin_tipster_access_bp, url_prefix='/admin-tipster-access')
bp.register_blueprint(cron_bp, url_prefix='/automate')
bp.register_blueprint(users_bp, url_prefix='/me')  # 👈 mapped to personal user actions
