from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSEventLog(Base):
    __tablename__ = 'OrchUKRCCQSEventLog'
    EventID = Column(BigInteger, primary_key=True, nullable=False) #bigint IDENTITY(1,1) NOT NULL,
    RequestStage = Column(String(50), nullable=False) #nvarchar(50) NOT NULL,
    RequestStatus = Column(String(50), nullable=False) #nvarchar(50) NOT NULL,
    ErrorStackTrace = Column(String) #nvarchar(max) NULL,   
    ErrorCode = Column(String(50)) #nvarchar(50) NULL,
    ErrorModule = Column(String(50)) #nvarchar(50) NULL,
    ErrorDescription = Column(String) #nvarchar(max) NULL,
    WarningCode = Column(String(50)) #nvarchar(50) NULL,
    WarningDescription = Column(String) #nvarchar(max) NULL,
    CorrelationID = Column(String) #nvarchar(max) NULL,
    ScoreRequestID = Column(String(30)) #nvarchar(30) NULL,
    OrchUKRCCQSInputScoreRequestID = Column(Integer) #int NULL,