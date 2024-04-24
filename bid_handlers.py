from flask import Blueprint

bid_handlers = Blueprint('bid_handlers', __name__, static_folder='static', template_folder='templates')

@bid_handlers.route('/<int:bid_id>')
def bid(bid_id):
    return "Bid page"