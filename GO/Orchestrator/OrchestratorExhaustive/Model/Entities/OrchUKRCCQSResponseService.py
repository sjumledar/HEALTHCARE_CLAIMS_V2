from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
from sqlalchemy import *

Base = declarative_base()

class OrchUKRCCQSResponseService(Base):
    __tablename__ = 'OrchUKRCCQSResponseService'
    OrchUKRCCQSResponseServiceID = Column(Integer, primary_key=True, autoincrement=True)
    ServiceName = Column(String(250), nullable=False) #nvarchar(250) NOT NULL,
    ServiceRequest = Column(String) #nvarchar(max) NOT NULL,
    ServiceResponse = Column(String) #nvarchar(max) NULL,
    ServiceStartTime = Column(String) #datetime NOT NULL,
    ServiceEndTime = Column(String) #datetime NULL,
    OverallStartTime = Column(String) #datetime NULL,
    OverallEndTime = Column(String) #datetime NULL,
    ScoreRequestID = Column(String(30)) #nvarchar(30) NULL,
    CorrelationID = Column(String) #nvarchar(max) NULL,
    HttpStatusCode = Column(String(100)) #nvarchar(100) NULL,
    CustomStatus = Column(String(500)) #nvarchar(500) NULL,
    RetryCount = Column(Integer) #int NULL,
    OrchUKRCCQSInputScoreRequestID = Column(Integer) #int NULL,