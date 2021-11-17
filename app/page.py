import os
from flask import render_template

def dir_last_updated(folder):
    return str(max(os.path.getmtime(os.path.join(root_path, f))
                   for root_path, dirs, files in os.walk(folder)
                   for f in files))

def generate_page(html_page, **kwargs):
    return render_template(html_page, last_updated=dir_last_updated('app/static/css'), **kwargs)
