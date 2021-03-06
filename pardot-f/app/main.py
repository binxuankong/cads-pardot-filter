import os
from flask import Flask, redirect, url_for, session, request, Response
from app.page import generate_page, generate_query
from app.update import get_token, update_pardot_db
from app.filter import get_skillstreet_filters, get_datastar_filters, filter_result
from app.config.settings import settings

app = Flask(__name__)
app.secret_key = b'\xf8`\xcc\xd7v@\xe5\xce\xcc4fQ\xe6h\xba\xd7\xca\x9d\xf6\xfb\x7f\x9c\xe6\xec'
base_route = '/pardot-filter'

@app.route('/', methods=['GET', 'POST'])
@app.route(base_route, methods=['GET', 'POST'])
def index():
    user = session.get('code', None)
    if request.method == 'POST' and user is not None:
        session['query'] = request.form
        query = generate_query(user) + '-' + str(len(request.form))
        return redirect(url_for('result', q=query))
    skillstreet_filters = get_skillstreet_filters()
    datastar_filters = get_datastar_filters()
    return generate_page('index.html', user=user, s_filters=skillstreet_filters, d_filters=datastar_filters)

@app.route('/login')
@app.route(base_route + '/login')
def login():
    auth_url = settings['AUTH_URL']
    client_id = settings['CLIENT_ID']
    redirect_uri = settings['REDIRECT_URI']
    auth_url += f'response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
    return redirect(auth_url)

@app.route('/logout')
@app.route(base_route + '/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/callback')
@app.route(base_route + '/callback')
def callback():
    code = request.args.get('code', None)
    if code is None:
        print('Error getting code.')
        return redirect(url_for('index'))
    session['code'] = code
    return redirect(url_for('update'))

@app.route('/update')
@app.route(base_route + '/update')
def update():
    code = session.get('code', None)
    if code is None:
        return redirect(url_for('login'))
    headers = get_token(code)
    if headers is None:
        print('Error getting auth token.')
        return redirect(url_for('index'))
    try:
        updated = update_pardot_db(headers)
        if updated:
            print('Successfully update Pardot DB.')
        else:
            print('No new Pardot data to update.')
        return redirect(url_for('index'))
    except Exception as e:
        print('Error in updating Pardot DB:', e)
        return redirect(url_for('index'))

@app.route('/result')
@app.route(base_route + '/result')
def result():
    user = session.get('code', None)
    query = request.args.get('q', None)
    form = session.get('query', None)
    if user is None or query is None or form is None:
        return redirect(url_for('index'))
    data = filter_result(form)
    if data is None:
        data = []
    else:
        data = data.to_dict('records')
    return generate_page('result.html', data=data, query=query, user=user)

@app.route('/download')
@app.route(base_route + '/download')
def download():
    user = session.get('code', None)
    query = request.args.get('q', None)
    type_ = request.args.get('type', None)
    form = session.get('query', None)
    if user is None or query is None or form is None:
        return redirect('/')
    if user is None or query is None or form is None or type_ is None:
        return redirect(url_for('index'))
    df = filter_result(form)
    if df is None:
        return redirect('/')
    filename = query + '.csv'
    if type_ == 'in':
        df = df.loc[~df['opted_out']]
    if type_ == 'out':
        df = df.loc[df['opted_out']]
    filename = query + '-' + type_ + '.csv'
    return Response(df.to_csv(index=False),
                    mimetype='text/csv',
                    headers={'Content-disposition': 'attachment; filename=' + filename}
                )
