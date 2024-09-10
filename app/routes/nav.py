import flask
from flask import render_template, request, redirect, url_for, Blueprint
from flask_login import current_user, login_required

nav_routes = Blueprint('nav', __name__, template_folder='templates', url_prefix="/")


@nav_routes.route("/", methods=["GET"])
def get_nav():
    return render_template("routes.html")
