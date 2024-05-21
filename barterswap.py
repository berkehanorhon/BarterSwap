import mimetypes
import os.path
from PIL import Image
from werkzeug.utils import secure_filename
import uuid
from datetime import datetime, timedelta

max_content_length = 5 * 1024 * 1024
ALLOWED_ADDITEM_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/jpg'}


def upload_and_give_name(path, image, allowed_types):
    if not image:
        raise Exception("No image uploaded!")
    mimetype = mimetypes.guess_type(image.filename)[0]
    if mimetype not in allowed_types:
        return 'Invalid file type', 415
    filename = secure_filename(image.filename)
    random_filename = str(uuid.uuid4()) + os.path.splitext(filename)[1]
    image_path = os.path.join(path, random_filename)
    foo = Image.open(image)
    foo = foo.resize((625, 700))
    foo.save(image_path, optimize=True, quality=95)

    print(image, type(image), image_path, random_filename)
    return random_filename

def set_end_time(hours):
    now = datetime.utcnow()
    end_time = now + timedelta(hours=hours)
    end_time = end_time.replace(minute=end_time.minute if end_time.second < 30 else end_time.minute + 1, second=55, microsecond=0)
    return end_time
