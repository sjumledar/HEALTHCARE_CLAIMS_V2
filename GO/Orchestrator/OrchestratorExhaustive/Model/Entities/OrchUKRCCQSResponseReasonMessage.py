from decimal import Decimal
from tokenize import Number
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSResponseReasonMessage(Base):
    __tablename__ = 'OrchUKRCCQSResponseReasonMessage'
    OrchUKRCCQSResponseReasonMessageID = Column(Integer, primary_key=True, autoincrement=True)
    PredictorId = Column(Integer)
    PredictorName = Column(String(100)) 
    ReasonGroupName = Column(String(80)) 
    ReasonGroupContribution = Column(Float) 
    ReasonMessageText = Column(String(250)) 
    MessageColor = Column(String(20)) 
    SAReasonMessageText = Column(String(250)) 
    CorrelationID = Column(String(80)) 
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 