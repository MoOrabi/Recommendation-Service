import uuid

from flask import Blueprint
from pandas import DataFrame
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text

from models.db import (get_job_seekers, get_job_posts, get_job_seekers_ready_to_json, job_post_df_ready_to_json,
                       get_job_posts_for_company, get_job_posts_for_recruiter, session, DeserializeHelper, convert_uuid_binary_to_str)
from models.JobSeekerJobPostScore import JobSeekerJobPostScore
import pandas as pd

apis = Blueprint('apis', __name__)

job_posts_df: DataFrame = get_job_posts()
job_seekers_df: DataFrame = get_job_seekers()


def combine_job_post_fields(row):
    return ((str(row['job_title']) if row['job_title'] else '') + ' ' +
            (str(row['job_title']) if row['job_title'] else '') + ' ' +
            (str(row['job_title']) if row['job_title'] else '') + ' ' +
            (str(row['min_experience_years']) if row['min_experience_years'] else '') + ' ' +
            (str(row['max_experience_years']) if row['max_experience_years'] else '') + ' ' +
            (str(row['requirements']) if row['requirements'] else '') + ' ' +
            (str(row['description']) if row['description'] else ''))


def combine_job_seeker_fields(row):
    return ((str(row['job_title']) if row['job_title'] else '') + ' ' +
            (str(row['career_level']) if row['career_level'] else '') + ' ' +
            (str(row['jobs_user_interested_in']) if row['jobs_user_interested_in'] else '') + ' ' +
            (str(row['years_of_experience']) if row['years_of_experience'] else '') + ' ' +
            (str(row['years_of_experience']) if row['years_of_experience'] else '') + ' ' +
            (str(row['skills']) if row['skills'] else '') + ' ' +
            (str(row['jobs_types_user_interested_in']) if row['jobs_types_user_interested_in'] else '') + ' '

            )

cosine_sim = None


def train_and_store():
    similarity_details = []
    job_posts_df['combined'] = job_posts_df.apply(combine_job_post_fields, axis=1)
    job_seekers_df['combined'] = job_seekers_df.apply(combine_job_seeker_fields, axis=1)

    tfidf_vectorizer = TfidfVectorizer(stop_words='english')

    # Fit and transform the job posts combined fields
    job_posts_tfidf_matrix = tfidf_vectorizer.fit_transform(job_posts_df['combined'])

    # Transform the job seekers combined fields (use the same vectorizer)
    job_seekers_tfidf_matrix = tfidf_vectorizer.transform(job_seekers_df['combined'])

    cosine_sim = cosine_similarity(job_seekers_tfidf_matrix, job_posts_tfidf_matrix)

    for seeker_idx in range(cosine_sim.shape[0]):
        for post_idx in range(cosine_sim.shape[1]):
            job_seeker_id = job_seekers_df.iloc[seeker_idx]['id']
            job_post_id = job_posts_df.iloc[post_idx]['id']
            score = cosine_sim[seeker_idx][post_idx]
            similarity_details.append((job_seeker_id, job_post_id, score))
    session.query(JobSeekerJobPostScore).delete()
    for row in similarity_details:
        instance = JobSeekerJobPostScore(job_seeker_id=uuid.UUID(row[0]).bytes, job_post_id=uuid.UUID(row[1]).bytes,
                                         score=row[2])
        session.add(instance)
    session.commit()
    # print(similarity_details)


def get_job_recommendations(job_seeker_id):
    query = (" * from job_post jp join job_seeker_job_post_score sc on jp.id = sc.job_post_id"
             " where sc.job_seeker_id = UUID_TO_BIN('") + job_seeker_id + "') order by sc.score desc"
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    df = job_post_df_ready_to_json(df)
    df['job_seeker_id'] = df['job_seeker_id'].apply(convert_uuid_binary_to_str)
    df['job_post_id'] = df['job_post_id'].apply(convert_uuid_binary_to_str)
    return df


def get_recommended_job_seekers(job_post_ids):
    job_post_ids = ["UUID_TO_BIN('"+str(uuid.UUID(bytes=row))+"'), " for row in job_post_ids]
    query = (" * from job_seeker js join job_seeker_job_post_score sc on js.id = sc.job_seeker_id"
             " where sc.job_post_id in (") + ''.join(job_post_ids)[:-2] + ") order by sc.score desc"
    print("Hi", ''.join(job_post_ids))
    df = pd.read_sql(session.query(text(query)).statement, session.bind)

    df = get_job_seekers_ready_to_json(df)
    df['job_seeker_id'] = convert_uuid_binary_to_str(df['job_seeker_id'])
    df['job_post_id'] = convert_uuid_binary_to_str(df['job_post_id'])
    return df


def get_recommended_job_seekers_for_employer(employer_id, employer_type):
    if employer_type == "ROLE_COMPANY":
        job_post_ids = get_job_posts_for_company(employer_id)
        return get_recommended_job_seekers(job_post_ids).to_json(orient="records")
    elif employer_type == "ROLE_RECRUITER":
        job_post_ids = get_job_posts_for_recruiter(employer_id)
        return get_recommended_job_seekers(job_post_ids).to_json(orient="records")


# print("Job Seekers", get_recommended_job_seekers_for_employer('50258f51-9eea-4a92-90c5-8bfd7bae6fd3', "ROLE_COMPANY"))

# print(get_job_recommendations('8d4fd53e-05e1-4be4-91f6-b1db66748f04').to_json(orient="records"))

# train_and_store()
