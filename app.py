import base64
from threading import Thread

from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, get_jwt

from myapi import recommendationSer
from config import scheduleTasks

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/hirexhire'

app.config["JWT_SECRET_KEY"] = base64.b64decode('404E635266556A586E3272357538782F413F4428472B4B6250645367566B5970')
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config["JWT_HEADER_TYPE"] = "Bearer"

jwt = JWTManager(app)


@app.route('/job-recommendation/<employer_type>/<page_number>/<page_size>', methods=['GET'])
@jwt_required()
def get_recommended_job_seekers(employer_type, page_number, page_size):
    user_id = get_jwt()['jti']
    return recommendationSer.get_recommended_job_seekers_for_employer(user_id, employer_type,
                                                                      page_number, page_size)


@app.route('/job-seekers-recommendation/<page_number>/<page_size>', methods=['GET'])
@jwt_required()
def get_recommended_job_posts(page_number, page_size):
    user_id = get_jwt()['jti']
    return recommendationSer.get_job_recommendations(user_id, page_number, page_size)


if __name__ == "__main__":
    t = Thread(target=scheduleTasks.run_schedule())
    t.start()

    app.run(debug=True)


