from flask import Blueprint

bp = Blueprint("admin", __name__, static_folder="static", template_folder="templates")

from app.admin.routes import main