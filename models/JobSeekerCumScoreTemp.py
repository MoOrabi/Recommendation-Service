import uuid

from sqlalchemy import Column, Float, BINARY
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class JobSeekerJobCumScoreTemp(Base):
    __tablename__ = 'job_seeker_cum_score_temp'
    id = Column(BINARY(16), primary_key=True, default=uuid.uuid4)
    cumulative_score = Column(Float)

