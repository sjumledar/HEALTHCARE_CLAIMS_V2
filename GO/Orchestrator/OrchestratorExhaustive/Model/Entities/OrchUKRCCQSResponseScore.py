from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy import *

Base = declarative_base()

class OrchUKRCCQSResponseScore(Base):
    __tablename__ = 'OrchUKRCCQSResponseScore'
    OrchUKRCCQSResponseScoreID = Column(Integer, primary_key=True, autoincrement=True)
    OverallScore = Column(String)
    ELScore = Column(String)
    GLScore = Column(String)
    PropScore = Column(String)   
    SubmissionNumber = Column(String) 
    Status = Column(String) 
    CorrelationID = Column(String) 
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 