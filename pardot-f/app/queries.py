select_query_map = {
    'skill': ', jss.skill_id as skill_id'
}

join_query_map = {
    'skill': 'join job_seeker_skills jss on jss.job_seeker_id = jsp.id',
    'studying': """join job_seeker_experience jse on jse.job_seeker_id = jsp.id
        join education e on e.job_seeker_experience_id = jse.id""",
    'employed': """join job_seeker_experience jse on jse.job_seeker_id = jsp.id
        join work_experience we on we.job_seeker_experience_id = jse.id"""
}

where_query_map = {
    'rubiqe': 'jsp.is_rubiqe',
    'acceltic': 'jsp.is_acceltic',
    'smart_skills': 'jsp.is_completed_smart_skills',
    'not_cads': "ud.user_id not ilike '%%@thecads.com' and ud.user_id not ilike '%%@yopmail.com'",
    'data_star': 'jsp.is_data_star',
    'studying': 'e.status and e.is_current',
    'employed': 'we.status and we.is_current',
    'preassessment': "pa.id notnull",
    'interview': """sa."Interviewed" = 'Y'""",
    'interview_recommend': """sa."Remarks" ilike 'recommend%%'""",
    'bumiputera': """a."Race" = 'Malay'""",
    'currently_employed': """jh."EmploymentStatus" = 'True'""",
}

skill_filter_query = 'select id, "name" from skill where status order by "name"'

country_filter_query = """
select c.id, c."name" 
from country c 
where exists (
	select from job_seeker_profile jsp where jsp.country_id = c.id
)
order by c."name" 
"""

datastar_applicant_filter_query = 'select distinct a."Age" from "Applicants" a order by "Age"'

datastar_alumni_filter_query = 'select distinct "Sponsor", "Cohort", "Year", "DSStatus", "Gender" from "DataStarAlumni"'

datastar_job_filter_query = 'select distinct "CompanyName", "SalaryRange" from "JobHistory" where "CurrentJob"'

pardot_query = """
select id, first_name, last_name, email, company, job_title, opted_out, updated_at
from "PardotProspect"
"""

skillstreet_query = """
select ud.user_id as "email" {}
from user_details ud
join job_seeker_profile jsp on jsp.user_details_id = ud.id {}
where jsp.status and ud.status and ud.activate
"""

datastar_applicant_query = """
select a."Email" as "email"
from "Applicants" a
left join "PreAssessments" pa on pa."ApplicantId" = a."ApplicantId"
left join "SelectionAssessments" sa on sa."ApplicantId" = a."ApplicantId"
where a."Email" notnull
"""

datastar_alumni_query = """
select dsa."EmailAddress" as "email"
from "DataStarAlumni" dsa
join "JobHistory" jh on jh."Id" = dsa."Id" 
where dsa."EmailAddress" notnull
"""

pardot_update_query = """
update "PardotProspect" pp
set salutation = ppt.salutation, first_name = ppt.first_name, last_name = ppt.last_name, email = ppt.email,
company = ppt.company, job_title = ppt.job_title, department = ppt.department, industry = ppt.industry,
address_one = ppt.address_one, address_two = ppt.address_two, city = ppt.city, zip = ppt.zip, state = ppt.state,
country = ppt.country, phone = ppt.phone, is_do_not_email = ppt.is_do_not_email, is_do_not_call = ppt.is_do_not_call,
opted_out = ppt.opted_out, created_at = ppt.created_at, updated_at = ppt.updated_at
from "PardotProspectTemp" ppt
where pp.id = ppt.id
"""

pardot_insert_query = """
insert into "PardotProspect"
(id, salutation, first_name, last_name, email, company, job_title, department, industry, address_one, address_two,
 city, zip, state, country, phone, is_do_not_email, is_do_not_call, opted_out, created_at, updated_at)
select
ppt.id, ppt.salutation, ppt.first_name, ppt.last_name, ppt.email, ppt.company, ppt.job_title, ppt.department,
ppt.industry, ppt.address_one, ppt.address_two, ppt.city, ppt.zip, ppt.state, ppt.country, ppt.phone,
ppt.is_do_not_email, ppt.is_do_not_call, ppt.opted_out, ppt.created_at, ppt.updated_at
from "PardotProspectTemp" ppt
on conflict (id) do nothing
"""