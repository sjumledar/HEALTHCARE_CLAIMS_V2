
from decimal import Decimal
from types import MappingProxyType
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *
import json
Base = declarative_base()

class OrchUKRCCQSOutputDnBService(Base):
    __tablename__ = 'OrchUKRCCQSOutputDnBService'
    OrchUKRCCQSOutputDnBServiceID = Column(Integer, primary_key=True, autoincrement=True)
    CorrelationID = Column(String(80))
    # DNBServiceRequest = Column(String(max))
    # DNBServiceResponse = Column(String(max))
    DunsNumber = Column(String(10))
    ConfidenceCode = Column(String(10))
    CPCT = Column(String(10))
    Error = Column(String(1000))
    AccountName = Column(String(500))
    StreetAddress1 = Column(String(500))
    StreetAddress2 = Column(String(500))
    City = Column(String(20))    
    ZipCode = Column(String(20))
    Country = Column(String(20))    
    Sourcesystem = Column(String(20))    
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 


class OrchUKRCCQSOldDnBService():
    def __init__(self):
        self.OrchUKRCCQSOutputDnBServiceID = None
        self.CorrelationID  = None
        self.DunsNumber = None
        self.ConfidenceCode  = None
        self.CPCT  = None
        self.Error = None
        self.AccountName = None
        self.StreetAddress1  = None
        self.StreetAddress2  = None
        self.City  = None
        self.ZipCode  = None
        self.Country = None
        self.Sourcesystem = None
        self.OrchUKRCCQSInputScoreRequestID  = None
