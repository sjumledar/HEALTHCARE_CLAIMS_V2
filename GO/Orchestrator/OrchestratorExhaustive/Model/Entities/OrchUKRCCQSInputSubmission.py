from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSInputSubmission(Base):
    __tablename__ = 'OrchUKRCCQSInputSubmission'
    OrchUKRCCQSInputSubmissionID = Column(Integer, primary_key=True, nullable=False)
    SubmissionNumber = Column(String(100))
    SubmissionCreateDate = Column(String)
    NatureOfBusiness = Column(String(1000))
    PropertyTotalExposureBanded = Column(String(100))
    PropertyClaimsHistory5YrsBinary = Column(String(10))
    # CreateDateTime  = Column(String, nullable=False)
    # ModifiedDateTime = Column(String)
    OrchUKRCCQSInputScoreRequestID = Column(Integer)
