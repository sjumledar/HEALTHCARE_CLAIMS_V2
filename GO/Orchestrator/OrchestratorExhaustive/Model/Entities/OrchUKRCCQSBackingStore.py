from decimal import Decimal
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSBackingStore(Base):
    __tablename__ = 'OrchUKRCCQSBackingStore'
    OrchUKRCCQSBackingStoreID = Column(Integer, primary_key=True, autoincrement=True)
    KeyField = Column(String(1000))
    ValueField = Column(String(1000)) 
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 