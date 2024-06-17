import base64

from flask import Flask, request
from models.db import get_job_seekers, get_job_posts
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, get_jwt
from myapi import recommendationSer

app = Flask(__name__)


app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/hirexhire'

app.config["JWT_SECRET_KEY"] = base64.b64decode('404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_HEADER_TYPE"] = "Bearer"

jwt = JWTManager(app)


@app.route('/job-recommendation/<employer_type>', methods=['GET'])
@jwt_required()
def get_recommended_job_seekers(employer_type):
    user_id = get_jwt()['jti']
    print(user_id)
    return recommendationSer.get_recommended_job_seekers_for_employer(user_id, employer_type)


@app.route('/job-seekers-recommendation/<job_seeker_id>', methods=['GET'])
@jwt_required()
def get_recommended_job_posts(job_seeker_id):
    user_id = get_jwt()['jti']
    print(user_id)
    return recommendationSer.get_job_recommendations(user_id)


if __name__ == "__main__":
    app.run(debug=True)


