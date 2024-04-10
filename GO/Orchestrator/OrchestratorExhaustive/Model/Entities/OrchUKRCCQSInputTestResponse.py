from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSInputTestResponse(Base):
    __tablename__ = 'OrchUKRCCQSInputTestResponse'
    OrchUKRCCQSInputTestResponseID = Column(Integer, primary_key=True, nullable=False) #int IDENTITY(1,1) NOT NULL,
    ServiceContractName = Column(String(100)) #nvarchar(100) NULL,
    ServiceContractTestRequest  = Column(String) #nvarchar(max) NULL,
    ServiceContractTestResponse = Column(String) #nvarchar(max) NULL,
    ServiceContractsToBeSkipped = Column(String(500)) #nvarchar(500) NULL,
    OrchUKRCCQSInputScoreRequestID = Column(Integer) #int NULL,
    # CreateDateTime = Column(String, nullable=False) #datetime NOT NULL,
    # ModifiedDateTime = Column(String) #datetime NULL,