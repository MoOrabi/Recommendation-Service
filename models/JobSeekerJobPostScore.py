import uuid
from sqlalchemy import create_engine, Column, Integer, String, Sequence, Float, BINARY
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.dialects.postgresql import UUID

class Base(DeclarativeBase):
    pass


class JobSeekerJobPostScore(Base):
    __tablename__ = 'job_seeker_job_post_score'
    job_seeker_id = Column(BINARY(16), primary_key=True, default=uuid.uuid4)
    job_post_id = Column(BINARY(16), primary_key=True, default=uuid.uuid4)
    score = Column(Float)

