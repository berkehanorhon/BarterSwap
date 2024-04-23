from flask import Blueprint, render_template

home_bp = Blueprint('home', __name__, static_folder='static', template_folder='templates')

@home_bp.route("/")
def home():
    return render_template('base.html')