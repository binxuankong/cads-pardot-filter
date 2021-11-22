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

def get_datastar_fileters():
    engine = create_engine(settings['DATASTAR_DB'], connect_args={'options': '-csearch_path={}'.format('cohort1to3')})
    df_app = pd.read_sql_query(datastar_applicant_filter_query, engine)
    df_alm = pd.read_sql_query(datastar_alumni_filter_query, engine)
    df_jh = pd.read_sql_query(datastar_job_filter_query, engine)
    engine.dispose()
    return {
        'age': df_app['Age'].unique().tolist(),
        'sponsor': sorted(df_alm['Sponsor'].unique().tolist()),
        'cohort': sorted(df_alm['Cohort'].unique().tolist()),
        'year': sorted(df_alm['Year'].unique().tolist()),
        'path': sorted(df_alm['DSStatus'].unique().tolist()),
        'gender': sorted(df_alm['Gender'].unique().tolist()),
        'company': sorted(df_jh['CompanyName'].dropna().unique().tolist()),
        'salary': sorted(df_jh['SalaryRange'].dropna().unique().tolist())
    }

def filter_result(form):
    # Get pardot data
    engine = create_engine(settings['PARDOT_DB'])
    df_p = pd.read_sql_query(pardot_query, engine)
    engine.dispose()

    select_query = ""
    join_query = ""
    where_query = ""
    is_info = False

    # Boolean filter
    for k in form.keys():
        col = form[k]
        if 'bool_' in k:
            if col == 'info':
                is_info = True
                continue
            if col in join_query_map.keys():
                join_query += "\n" + join_query_map[col]
            where_query += " and " + where_query_map[col]
            is_info = True
    
    # Skill filter
    skill_ids = [form[f] for f in form if 'skill_' in f]
    all_skills = False
    if form['all_skill'] == 'true':
        all_skills = True
    if len(skill_ids) > 0:
        select_query += select_query_map['skill']
        join_query += "\n" + join_query_map['skill']
        where_query += " and jss.skill_id in ({})".format(','.join(skill_ids))
    
    # Country filter
    country_ids = [form[f] for f in form if 'country_' in f]
    if len(country_ids) > 0:
        where_query += " and jsp.country_id in ({})".format(','.join(country_ids))

    # Get skillstreet data
    engine = create_engine(settings['SKILLSTREET_PROD'])
    df_s = pd.read_sql_query(skillstreet_query.format(select_query, join_query) + where_query, engine)
    engine.dispose()
    if len(skill_ids) > 0:
        df_s['skill_id'] = df_s['skill_id'].astype('category')
        df_s = df_s.pivot_table(index='user_id', columns='skill_id', aggfunc=lambda x: ' '.join(x))
        df_s = df_s.rename(columns=str).reset_index()
        if all_skills:
            df_s = df_s.dropna(subset=skill_ids)
    
    # Merge pardot data with skillstreet data
    df = df_p.merge(df_s[['user_id']].drop_duplicates(), left_on='email', right_on='user_id', how='left')
    if is_info:
        df = df.dropna(subset=['user_id'])
    # df = df[['id', 'name', 'email', 'company', 'job_title', 'opted_out', 'updated_at']]
    df = df.drop(columns=['user_id'])
    return df

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
