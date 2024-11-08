from sqlalchemy import create_engine
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import sessionmaker
import uuid
import javaobj as javaobj


user, password, host, database = 'root', 'root', 'localhost', 'hirexhire'
engine = create_engine(url=f'mysql+pymysql://{user}:{password}@{host}/{database}?charset=utf8')

connection = engine.connect()

Session = sessionmaker(bind=engine)
session = Session()


# Function to convert binary UUID to string
def convert_uuid_binary_to_str(uuid_binary):
    return str(uuid.UUID(bytes=uuid_binary))


def get_job_posts():
    query = " * from job_post"
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    if len(df.values) == 0:
        return []
    df = job_post_df_ready_to_json(df)

    return df


def job_post_df_ready_to_json(df):
    df['id'] = df['id'].apply(convert_uuid_binary_to_str)
    df['company_id'] = df['company_id'].apply(convert_uuid_binary_to_str)
    df['creator_id'] = df['creator_id'].apply(convert_uuid_binary_to_str)
    return df


def get_job_posts_for_company(company_id):
    query = (" * from job_post jp join job_seeker_job_post_score sc on jp.id = sc.job_post_id"
             " where company_id = UUID_TO_BIN('") + company_id + "')"
    df = pd.read_sql(session.query(text(query)).statement, session.bind)

    return df['id']


def get_job_posts_for_recruiter(recruiter_id):
    query = (" distinct id from job_post jp join job_seeker_job_post_score sc on jp.id = sc.job_post_id "
             "join recruiters_team rt on jp.id = rt.job_post_id "
             "where UUID_TO_BIN('") + recruiter_id + "') = rt.recruiter_id"
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    return df['id']


def get_job_seekers():
    query = " * from job_seeker"
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    if len(df.values) == 0:
        return []
    df = get_job_seekers_ready_to_json(df)

    return df


def get_job_seekers_ready_to_json(df):
    df['id'] = df['id'].apply(convert_uuid_binary_to_str)
    for i in range(len(df['jobs_user_interested_in'])):
        if df['jobs_user_interested_in'][i] is not None:
            df['jobs_user_interested_in'][i] = javaobj.loads(df['jobs_user_interested_in'][i])
    for i in range(len(df['jobs_types_user_interested_in'])):
        if df['jobs_types_user_interested_in'][i] is not None:
            df['jobs_types_user_interested_in'][i] = javaobj.loads(
                df['jobs_types_user_interested_in'][i])
    for i in range(len(df['skills'])):
        if df['skills'][i] is not None:
            df['skills'][i] = javaobj.loads(df['skills'][i])
    for i in range(len(df['work_samples'])):
        if df['work_samples'][i] is not None:
            df['work_samples'][i] = javaobj.loads(df['work_samples'][i])
    return df
