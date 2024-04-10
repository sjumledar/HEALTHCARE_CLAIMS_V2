from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import *

Base = declarative_base()

class OrchUKRCCQSInputClientInfo(Base):
    __tablename__ = 'OrchUKRCCQSInputClientInfo'
    OrchUKRCCQSInputClientInfoID = Column(Integer, primary_key=True, nullable=False) #int IDENTITY(1,1) NOT NULL,
    ClientNumber = Column(Integer)
    ClientName = Column(String(150)) 
    ClientLocationHouseNumberStreetName = Column(String(1000))
    ClientLocationLocalityName = Column(String(100))
    ClientLocationTown = Column(String(100))
    ClientLocationPostalCode = Column(String(50))
    ClientLocationCountry = Column(String(20))
    OrchUKRCCQSInputScoreRequestID = Column(Integer) 
