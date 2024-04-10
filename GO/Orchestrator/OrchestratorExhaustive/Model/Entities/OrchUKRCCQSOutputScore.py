from decimal import Decimal
from decimal import Decimal
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSOutputScore(Base):
    __tablename__ = 'OrchUKRCCQSOutputScore'
    OrchUKRCCQSOutputScoreID = Column(Integer, primary_key=True, autoincrement=True)
    POSTExhaustiveScoreOutputJson = Column(String(max))
    POSTScoreOutputJson = Column(String(max)) 
    CorrelationID = Column(String(80))  
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 