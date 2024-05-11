from flask import Flask, render_template,request,jsonify,redirect,url_for

from bid_handlers import bid_handlers
from home import home
from user_handlers import user_handlers
from item_handlers import item_handlers
from home import home_bp
from errorhandler import error_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['MAX_CONTENT_LENGTH'] = 4 * 1024 * 1024  # 4 MB
app.secret_key = 'your_secret_key_here'

app.register_blueprint(error_bp)
app.register_blueprint(home_bp, url_prefix='/')
app.register_blueprint(user_handlers,url_prefix='/user')
app.register_blueprint(item_handlers,url_prefix='/items')
app.register_blueprint(bid_handlers, url_prefix='/items/bid')


if __name__ == '__main__':
    app.run(debug=True)
