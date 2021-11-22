#!/bin/sh

gunicorn -w 2 -b 0.0.0.0:8055 wsgi:app