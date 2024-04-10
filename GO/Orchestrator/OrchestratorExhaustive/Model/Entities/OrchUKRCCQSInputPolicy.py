from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSInputPolicy(Base):
    __tablename__= 'OrchUKRCCQSInputPolicy'
    OrchUKRCCQSInputPolicyID  = Column(Integer, primary_key=True, nullable=False) #int IDENTITY(1,1) NOT NULL,
    PolicyNumber = Column(String(100))
    EffectiveDate = Column(String)
    ExpirationDate = Column(String)
    # CreateDateTime = Column(String, nullable=False) #datetime NOT NULL,
    # ModifiedDateTime = Column(String) #datetime NULL,
    OrchUKRCCQSInputScoreRequestID = Column(Integer) #int NULL,
