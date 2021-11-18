# from os import environ
from environ import environ

settings = {
    'CLIENT_ID': environ['CLIENT_ID'],
    'CLIENT_SECRET': environ['CLIENT_SECRET'],
    'BUSINESS_UNIT_ID': environ['BUSINESS_UNIT_ID'],
    'URL': environ['URL'],
    'AUTH_URL': environ['AUTH_URL'],
    'REDIRECT_URI': environ['REDIRECT_URI'],
    'PARDOT_DB': environ['PARDOT_DB'],
    'SKILLSTREET_PROD': environ['SKILLSTREET_PROD'],
    'DATASTAR_DB': environ['DATASTAR_DB'],
}
