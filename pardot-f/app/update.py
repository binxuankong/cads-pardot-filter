import pandas as pd
import requests
from sqlalchemy import create_engine
from app.queries import *
from app.config.settings import settings

def get_token(code):
    params = {
        'code': code,
        'grant_type': 'authorization_code',
        'client_id': settings['CLIENT_ID'],
        'client_secret': settings['CLIENT_SECRET'],
        'redirect_uri': settings['REDIRECT_URI']
    }
    url = f'https://login.salesforce.com/services/oauth2/token'
    try:
        response = requests.post(url, params=params)
        access_token = response.json().get('access_token')
        headers = {"Authorization": "Bearer " + access_token, "Pardot-Business-Unit-Id": settings['BUSINESS_UNIT_ID']}
        return headers
    except:
        return None

def update_pardot_db(headers):
    engine = create_engine(settings['PARDOT_DB'])
    df = pd.read_sql_query('select max(updated_at) from "PardotProspect"', engine)
    max_date = df['max'].max().strftime('%c')
    field = 'Prospect'
    version = 4
    operation = 'query'
    pardot_url = f'https://pi.pardot.com/api/{field}/version/{version}/do/{operation}?'
    fields = ['id', 'salutation', 'first_name', 'last_name', 'email', 'company', 'job_title', 'department', 'industry',
          'address_one', 'address_two', 'city', 'zip', 'state', 'country', 'phone', 'is_do_not_email', 'is_do_not_call',
          'opted_out', 'created_at', 'updated_at']
    fields = ','.join(fields)
    i = 0
    all_res = []
    while True:
        url = pardot_url + f'ouput=bulk&format=json&updated_after={max_date}&fields={fields}&offset={i}'
        res = requests.get(url, headers=headers)
        if res.json()['result'] is None or 'prospect' not in res.json()['result']:
            break
        all_res.extend(res.json()['result']['prospect'])
        i += 200
    df = pd.DataFrame.from_dict(all_res)
    df = df.drop_duplicates(subset=['email'])
    df['created_at'] = pd.to_datetime(df['created_at'])
    df['updated_at'] = pd.to_datetime(df['updated_at'])
    df['is_do_not_email'].fillna(0, inplace=True)
    df['is_do_not_call'].fillna(0, inplace=True)
    df['opted_out'].fillna(0, inplace=True)
    df = df.replace({1: True, 0: False})
    print(len(df))
    df.to_sql('PardotProspectTemp', engine, index=False, if_exists='replace')
    engine.execute(pardot_update_query)
    engine.execute(pardot_insert_query)
    engine.dispose()
    return
