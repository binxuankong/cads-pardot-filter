import os
from flask import Flask, redirect, session, request, Response
from app.page import generate_page
from app.update import get_token, update_pardot_db
from app.filter import get_skillstreet_filters, get_datastar_fileters, process_form, filter_result
from secrets import secrets

app = Flask(__name__)
app.secret_key = os.urandom(24)

@app.route('/', methods=['GET', 'POST'])
def index():
    session['code'] = 'dev'
    user = session.get('code', None)
    if request.method == 'POST':
        session['query'] = request.form
        print(request.form)
        print(process_form(request.form))
        return redirect('/')
        # return redirect(url_for('result', q=process_form(request.form)))
    skillstreet_filters = get_skillstreet_filters()
    datastar_filters = get_datastar_fileters()
    return generate_page('index.html', user=user, s_filters=skillstreet_filters, d_filters=datastar_filters)

@app.route('/login')
def login():
    auth_url = secrets['AUTH_URL']
    client_id = secrets['CLIENT_ID']
    redirect_uri = secrets['REDIRECT_URI']
    auth_url += f'response_type=code&client_id={client_id}&redirect_uri={redirect_uri}'
    return redirect(auth_url)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/callback')
def callback():
    code = request.args.get('code', None)
    if code is None:
        print('Error getting code.')
        return redirect('/')
    session['code'] = code
    return redirect('/update')

@app.route('/update')
def update():
    code = session.get('code', None)
    if code is None:
        return redirect('/login')
    headers = get_token(code)
    if headers is None:
        print('Error getting auth token.')
        return redirect('/')
    try:
        update_pardot_db(headers)
        print('Successfully update Pardot DB.')
        return redirect('/')
    except Exception as e:
        print('Error in updating Pardot DB:', e)
        return redirect('/')

@app.route('/result')
def result():
    user = session.get('code', None)
    query = request.args.get('q', None)
    form = session.get('query', None)
    if user is None or query is None or form is None:
        return redirect('/')
    data = filter_result(form).to_dict('records')
    return generate_page('result.html', data=data, query=query, user=user)

@app.route('/download')
def download():
    user = session.get('code', None)
    query = request.args.get('q', None)
    form = session.get('query', None)
    if user is None or query is None or form is None:
        return redirect('/')
    df = filter_result(form)
    filename = query + '.csv'
    return Response(df.to_csv(index=False),
                    mimetype='text/csv',
                    headers={'Content-disposition': 'attachment; filename=' + filename}
    )
