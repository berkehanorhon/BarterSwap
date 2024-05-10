from flask import Blueprint

error_bp = Blueprint('errors', __name__)


@error_bp.app_errorhandler(413)
def file_too_large(e):
    return "The file you tried to upload is too large. Maximum file size is 4MB.", 413
