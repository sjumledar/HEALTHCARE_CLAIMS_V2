from datetime import date, datetime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import *
from sqlalchemy.orm import *


Base = declarative_base()

class OrchUKRCCQSInputScoreRequest(Base):
    __tablename__ = "OrchUKRCCQSInputScoreRequest"
    OrchUKRCCQSInputScoreRequestID = Column(Integer, primary_key=True, autoincrement=True)
    CorrelationID = Column(String)
    ScoreRequestID = Column(String(30))
    TransactionType = Column(String(20))
    TransactionTimeStamp = Column(String)
    SourceSystem = Column(String(30))
    SourceSystemAction = Column(String(30))
    InputJsonText = Column(String)
    Context = Column(String(30))
    ProductType = Column(String(100))
    CreateDateTime = Column(String, nullable=False)
    ModifiedDateTime = Column(String)
    IsBulk = Column(String(1))

