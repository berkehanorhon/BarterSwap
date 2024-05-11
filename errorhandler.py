from flask import Blueprint
import barterswap

error_bp = Blueprint('errors', __name__)

max_content_legth = barterswap.max_content_length


@error_bp.app_errorhandler(413)
def file_too_large(e):
    return "The file you tried to upload is too large. Maximum file size is %sMB." % (
                max_content_legth // (1024 * 1024)), 413
