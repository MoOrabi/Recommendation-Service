import uuid

from flask import Blueprint
from pandas import DataFrame
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy import text

from models.db import (get_job_seekers, get_job_posts, get_job_seekers_ready_to_json, job_post_df_ready_to_json,
                       get_job_posts_for_company, get_job_posts_for_recruiter, session, DeserializeHelper, convert_uuid_binary_to_str)
from models.JobSeekerJobPostScore import JobSeekerJobPostScore
from models.JobSeekerCumScoreTemp import JobSeekerJobCumScoreTemp
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


def get_job_recommendations(job_seeker_id, page_number, page_size):
    query = (" * from job_post jp join job_seeker_job_post_score sc on jp.id = sc.job_post_id"
             " where sc.job_seeker_id = UUID_TO_BIN('" + job_seeker_id + "') order by sc.score desc"
             " limit " + str(page_size) + " offset " + str((page_number - 1) * page_size))
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    df = job_post_df_ready_to_json(df)
    df['job_seeker_id'] = df['job_seeker_id'].apply(convert_uuid_binary_to_str)
    df['job_post_id'] = df['job_post_id'].apply(convert_uuid_binary_to_str)
    return df


def get_recommended_job_seekers(job_seekers_ids, page_number, page_size):
    page_number = int(page_number)
    page_size = int(page_size)
    query = (" js.id , first_name, last_name, job_title, career_level, profile_photo, skills, "
             "degree, field_of_study, place , je1.name, start_year, end_year, cumulative_score "
             "from job_seeker js join job_seeker_cum_score_temp tmp on tmp.id = js.id "
             "left join education edu1 on edu1.job_seeker_id = js.id "
             "left join job_experience je1 on je1.job_seeker_id = js.id "
             "where (edu1.id = "
             "(select id from education edu2 where job_seeker_id = js.id order by start desc limit 1) or "
             "(select id from education edu2 where job_seeker_id = js.id order by start desc limit 1) is null) "
             "and (je1.id = "
             "(select id from job_experience je2 where je2.job_seeker_id = js.id "
             "order by start_year desc limit 1) or "
             "(select id from job_experience je2 where je2.job_seeker_id = js.id "
             "order by start_year desc limit 1) is null) " +
             " and js.id in (" + ''.join(job_seekers_ids)[:-2] + ") order by cumulative_score desc" +
             " limit " + str(page_size) + " offset " + str((page_number-1)*page_size))
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    print(len(df['id']))
    df['id'] = df['id'].apply(convert_uuid_binary_to_str)
    for i in range(len(df['skills'])):
        if df['skills'][i] is not None:
            df['skills'][i] = DeserializeHelper.deserialize(df['skills'][i])
    return df


def get_recommended_job_seekers_ids_with_cum_score(job_post_ids):
    job_post_ids = ["UUID_TO_BIN('"+str(uuid.UUID(bytes=row))+"'), " for row in job_post_ids]
    cumulative_job_seekers_scores = {}
    query = (" * from job_seeker_job_post_score sc " +
             " where sc.job_post_id in (" + ''.join(job_post_ids)[:-2] + ") ")
    print("Hi", ''.join(job_post_ids))
    df = pd.read_sql(session.query(text(query)).statement, session.bind)
    df['job_seeker_id'] = df['job_seeker_id'].apply(convert_uuid_binary_to_str)
    df['job_post_id'] = df['job_post_id'].apply(convert_uuid_binary_to_str)
    for i in range(len(df['job_seeker_id'])):
        if df['job_seeker_id'][i] not in cumulative_job_seekers_scores:
            cumulative_job_seekers_scores[df['job_seeker_id'][i]] = df['score'][i]
        else:
            cumulative_job_seekers_scores[df['job_seeker_id'][i]] += int(df['score'][i])
    session.query(JobSeekerJobCumScoreTemp).delete()
    for x in cumulative_job_seekers_scores.keys():
        score = JobSeekerJobCumScoreTemp(id=uuid.UUID(x).bytes,
                                         cumulative_score=cumulative_job_seekers_scores[x])
        session.add(score)
    session.commit()
    job_seekers_ids_with_score = sorted(cumulative_job_seekers_scores.items(), key=lambda x: x[1], reverse=True)
    job_seekers_ids = ["UUID_TO_BIN('"+str(row[0])+"'), " for row in job_seekers_ids_with_score]

    print(''.join(job_seekers_ids))
    return ''.join(job_seekers_ids)


def get_recommended_job_seekers_for_employer(employer_id, employer_type, page_number, page_size):
    job_post_ids = None
    if employer_type == "ROLE_COMPANY":
        job_post_ids = get_job_posts_for_company(employer_id)
    elif employer_type == "ROLE_RECRUITER":
        job_post_ids = get_job_posts_for_recruiter(employer_id)
    job_seekers_ids = get_recommended_job_seekers_ids_with_cum_score(job_post_ids)

    detailed_recommendations = get_recommended_job_seekers(job_seekers_ids, page_number, page_size).to_json(orient="records")
    return detailed_recommendations


# print("Job Seekers", get_recommended_job_seekers_for_employer('50258f51-9eea-4a92-90c5-8bfd7bae6fd3', "ROLE_COMPANY", 1,
#                                                               5))

# print(get_job_recommendations('8d4fd53e-05e1-4be4-91f6-b1db66748f04', 1, 5).to_json(orient="records"))



# train_and_store()
