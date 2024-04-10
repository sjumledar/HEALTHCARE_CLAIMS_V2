from decimal import Decimal
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSResponsePredictor(Base):
    __tablename__ = 'OrchUKRCCQSResponsePredictor'
    OrchUKRCCQSPredictorResponseID = Column(Integer, primary_key=True, autoincrement=True)
    PredictorId = Column(Integer)
    PredictorName = Column(String(100)) 
    PredictorRawValue = Column(String(80)) 
    PredictorBinValue = Column(Float) 
    ReasonGroupName = Column(String(250)) 
    CorrelationID = Column(String(80)) 
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 