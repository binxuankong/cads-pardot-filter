import os
import string
import random
from datetime import datetime as dt
from flask import render_template

def generate_page(html_page, **kwargs):
    return render_template(html_page, last_updated=dir_last_updated('app/static/css'), **kwargs)

def generate_query(code):
    s1 = dt.now().strftime('%y%m%d')
    s2 = dt.now().strftime('%H%M%S')
    s3 = code[:6]
    s4 = ''.join(random.choices(string.ascii_lowercase + string.ascii_uppercase + string.digits, k=6))
    return s1 + '-' + s2 + '-' + s3 + '-' + s4

def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))
