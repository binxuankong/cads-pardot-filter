import pandas as pd
from sqlalchemy import create_engine
from app.queries import *
from app.config.settings import settings

def get_skillstreet_filters():
    engine = create_engine(settings['SKILLSTREET_PROD'])
    df_s = pd.read_sql_query(skill_filter_query, engine)
    df_c = pd.read_sql_query(country_filter_query, engine)
    engine.dispose()
    return {
        'skill': df_s.to_dict('records'),
        'country': df_c.to_dict('records'),
    }

def get_datastar_filters():
    engine = create_engine(settings['DATASTAR_DB'], connect_args={'options': '-csearch_path={}'.format('cohort1to3')})
    df_app = pd.read_sql_query(datastar_applicant_filter_query, engine)
    df_alm = pd.read_sql_query(datastar_alumni_filter_query, engine)
    df_jh = pd.read_sql_query(datastar_job_filter_query, engine)
    engine.dispose()
    salary = df_jh['SalaryRange'].dropna().unique().tolist()
    salary.sort(key=lambda x: int(x.split(',')[0]))
    df_app.fillna('-', inplace=True)
    df_alm.fillna('-', inplace=True)
    df_jh.fillna('-', inplace=True)
    return {
        'age': df_app['Age'].unique().tolist(),
        'sponsor': sorted(df_alm['Sponsor'].unique().tolist()),
        'cohort': sorted(df_alm['Cohort'].unique().tolist()),
        'year': sorted(df_alm['Year'].unique().tolist()),
        'path': sorted(df_alm['DSStatus'].unique().tolist()),
        'gender': sorted(df_alm['Gender'].unique().tolist()),
        'company': sorted(df_jh['CompanyName'].dropna().unique().tolist()),
        'salary': salary,
    }

def filter_result(form):
    # Get pardot data
    engine = create_engine(settings['PARDOT_DB'])
    df = pd.read_sql_query(pardot_query, engine)
    engine.dispose()

    ss_select_query = ""
    ss_join_query = ""
    ss_where_query = app_where_query = alm_where_query = ""
    ss_params = app_params = alm_params = {}
    is_info = is_applicant = is_alumni = False

    # Iterate through filter
    for k in form.keys():
        col = form[k]
        if 'bool_' in k:
            if col == 'info':
                is_info = True
                continue
            if col in join_query_map.keys():
                ss_join_query += "\n" + join_query_map[col]
            ss_where_query += " and " + where_query_map[col]
            is_info = True
        if 'applicant' in k:
            is_applicant = True
            if col in where_query_map.keys():
                app_where_query += ' and ' + where_query_map[col]
        if 'alumni' in k:
            is_alumni = True
            if col in where_query_map.keys():
                alm_where_query += 'and ' + where_query_map[col]
    
    # Skill filter
    skill_ids = [form[f] for f in form if 'skill_id' in f]
    all_skills = False
    if form['all_skill'] == 'true':
        all_skills = True
    q, t = process_where_in(form, 'ss', 'jss', 'skill_id')
    if q is not None and t is not None:
        ss_select_query += select_query_map['skill']
        ss_join_query += "\n" + join_query_map['skill']
        ss_where_query += q
        ss_params[t[0]] = t[1]
    
    # Country filter
    q, t = process_where_in(form, 'ss', 'jsp', 'country_id')
    if q is not None and t is not None:
        ss_where_query += q
        ss_params[t[0]] = t[1]

    # Range filters
    app_where_query += process_where_range(form, 'ds', 'a', 'Age')

    # Where in filters
    where_in = [('ds', 'dsa', 'Cohort'), ('ds', 'dsa', 'DSStatus'), ('ds', 'dsa', 'Gender'), ('ds', 'dsa', 'Sponsor'),
                ('ds', 'dsa', 'Year')]
    for w in where_in:
        q, t = process_where_in(form, w[0], w[1], w[2])
        if q is not None and t is not None:
            alm_where_query += q
            alm_params[t[0]] = t[1]

    # Skillstreet filter
    if is_info:
        engine = create_engine(settings['SKILLSTREET_PROD'])
        query = skillstreet_query.format(ss_select_query, ss_join_query) + ss_where_query
        df_temp = pd.read_sql_query(query, engine, params=ss_params)
        engine.dispose()
        if len(skill_ids) > 0:
            df_temp['skill_id'] = df_temp['skill_id'].astype('category')
            df_temp = df_temp.pivot_table(index='email', columns='skill_id', aggfunc=lambda x: ' '.join(x))
            df_temp = df_temp.rename(columns=str).reset_index()
            if all_skills:
                df_temp = df_temp.dropna(subset=skill_ids)
        # Merge pardot data with skillstreet data
        df = df.merge(df_temp[['email']].drop_duplicates(), how='inner')
    
    # Datastar applicant filter
    if is_applicant:
        engine = create_engine(settings['DATASTAR_DB'], connect_args={'options': '-csearch_path={}'.format('cohort1to3')})
        query = datastar_applicant_query + app_where_query
        df_temp = pd.read_sql_query(query, engine, params=app_params)
        engine.dispose()
        df = df.merge(df_temp.drop_duplicates(), how='inner')
    
    # Datastar alumni filter
    if is_alumni:
        engine = create_engine(settings['DATASTAR_DB'], connect_args={'options': '-csearch_path={}'.format('cohort1to3')})
        query = datastar_alumni_query + alm_where_query
        df_temp = pd.read_sql_query(query, engine, params=alm_params)
        engine.dispose()
        df = df.merge(df_temp.drop_duplicates(), how='inner')

    return df

def process_where_range(form, db, table, feat):
    query = ''
    try:
        tmin = int(form[db + '_range_min_' + feat])
        tmax = int(form[db + '_range_max_' + feat])
        if tmin == -1 and tmax == -1:
            return query
        query = ' and {}."{}" = {}'
        if tmin == -1:
            return query.format(table, feat, tmax)
        if tmax == -1:
            return query.format(table, feat, tmin)
        return ' and {}."{}" between {} and {}'.format(table, feat, tmin, tmax)
    except:
        return query

def process_where_in(form, db, table, feat):
    match = db + '_in_' + feat
    feats = [form[f] for f in form if match in f]
    if len(feats) < 1:
        return None, None
    return ' and {}."{}" in %({})s'.format(table, feat, feat), (feat, tuple(feats))

def process_form(form):
    filter = ''
    skills = ''
    countries = ''
    for k in form.keys():
        if 'bool_' in k:
            filter += form[k] + '&'
        elif k == 'all_skill':
            if form[k] == 'true':
                skills = 'all_skills_('
            else:
                skills = 'any_skills_('
        elif 'skill_' in k:
            skills += '_'.join(k.split('_')[-1].lower().split()) + '&'
        elif 'country_' in k:
            countries += '_'.join(k.split('_')[-1].lower().split()) + '&'
        else:
            filter += k + '_' + form[k] + '&'
    if len(filter) < 1:
        return 'all'
    if len(skills) > 16:
        filter += skills.strip('&') + ')'
    if len(countries) > 0:
        filter += 'country_(' + countries.strip('&') + ')'
    return filter.strip('&')
