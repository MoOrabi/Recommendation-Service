import uuid

from sqlalchemy import Column, Float, BINARY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class JobSeekerJobPostScore(Base):
    __tablename__ = 'job_seeker_job_post_score'
    job_seeker_id = Column(BINARY(16), primary_key=True, default=uuid.uuid4)
    job_post_id = Column(BINARY(16), primary_key=True, default=uuid.uuid4)
    score = Column(Float)

