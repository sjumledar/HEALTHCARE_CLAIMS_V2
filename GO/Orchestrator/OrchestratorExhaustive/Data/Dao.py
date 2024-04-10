import logging
import threading
from datetime import datetime

from shared_code import Constants
from shared_code.helper_functions import *
from shared_code.ModelPredictorCatalog import *
from sqlalchemy.orm import *

from ..Model import *
from ..Model.CodeDesc import CodeDesc
from ..Model.CodeDescModule import CodeDescModule
from ..Model.Entities import *
from ..Model.Entities.OrchUKRCCQSBackingStore import *
from ..Model.Entities.OrchUKRCCQSEventLog import *
from ..Model.Entities.OrchUKRCCQSInputClientInfo import *
from ..Model.Entities.OrchUKRCCQSInputPolicy import *
from ..Model.Entities.OrchUKRCCQSInputScoreRequest import *
from ..Model.Entities.OrchUKRCCQSInputSubmission import *
from ..Model.Entities.OrchUKRCCQSInputTestResponse import *
from ..Model.Entities.OrchUKRCCQSOutputScore import *
from ..Model.Entities.OrchUKRCCQSResponsePredictor import *
from ..Model.Entities.OrchUKRCCQSResponseReasonMessage import *
from ..Model.Entities.OrchUKRCCQSResponseScore import *
from ..Model.Entities.OrchUKRCCQSResponseService import *

engine = create_azsql_engine("SAOp")

def get_session(engine) :
    try:
        conn = engine.connect() #test if engine is up
        conn.close() #return conn to connection pool
    except Exception as e:
        print(e)
        engine = create_azsql_engine("SAOp") # if engine test failed, create an engine  

    session = Session(engine)

    return session
    

class CommitThread (threading.Thread):
    def __init__(self, objToSave, name, qsRequest : OrchUKRCCQSRequest.OrchUKRCCQSRequest = None):
       threading.Thread.__init__(self)
       self.objToSave = objToSave
       self.name = name
       self.qsRequest = qsRequest
       
    def run(self):
       CommitChange(self.objToSave, self.name, self.qsRequest)

def CommitChange(objToSave, name, qsRequest : OrchUKRCCQSRequest.OrchUKRCCQSRequest = None):
    #print("CommitChange started")
    try:
        engine = create_azsql_engine("SAOp")
        session = Session(engine)
        session.add(objToSave)
        session.commit()  
    except Exception as e:        
        processerror(qsRequest, e, name)  

class commitAllSessionChanges(threading.Thread): 
    def __init__(self, session): 
        threading.Thread.__init__(self) 
        self.session = session 
    
    def run(self): 
        self.session.commit() 

def processerror(qsRequest, e, name):
    dataSaveErrors =[]
    for	x in range(0,len(e.args)):
        create_errors_collection("DataSaveError", e.args[x], dataSaveErrors)
    for	dataSaveError in dataSaveErrors: 
        print(dataSaveError)
        if(qsRequest!=None):   
            SaveToEventLog(qsRequest.ScoreRequestInputID, "RequestStage_SaveData", "Status_Failed", "DataSaveError", "dao.CommitChange", "Error in saving input data " + name + " " + str(e), CorrelationID = str(qsRequest.CorrelationID), ScoreRequestID =qsRequest.ScoreRequestInput.ScoreRequestID )
            qsRequest.Errors.append(CodeDesc (Code = "DataSaveError", Description = "Error in saving input data " + name  + " " + dataSaveError))

def logerror(e):
    dataSaveErrors =[]
    for	x in range(0,len(e.args)):
        create_errors_collection("DataSaveError", e.args[x], dataSaveErrors)
    for	dataSaveError in dataSaveErrors: 
        logging.info(dataSaveError)
      
def SaveToEventLog(
    scoreRequestInputID: int,
    RequestStage: str =null(),
    RequestStatus: str =null(),
    ErrorCode: str  =null(),
    ErrorModule: str  =null(),
    ErrorDescription: str  =null(),
    WarningCode: str =null(),
    WarningDescription: str  =null(),
    ErrorStackTrace: str  =null(),
    CorrelationID: str = "",
    ScoreRequestID: str = ""
    ):
    eventLog = OrchUKRCCQSEventLog(
        RequestStage = RequestStage,
        RequestStatus = RequestStatus,
        ErrorCode = ErrorCode,
        ErrorDescription = ErrorDescription,
        ErrorModule = ErrorModule,
        WarningCode = WarningCode,
        WarningDescription = WarningDescription,
        ErrorStackTrace = ErrorStackTrace,
        CorrelationID = str(CorrelationID),
        ScoreRequestID = ScoreRequestID
    )
    if scoreRequestInputID is not null:
        eventLog.OrchUKRCCQSInputScoreRequestID = scoreRequestInputID
    thread1 = CommitThread(eventLog, "OrchUKRCCQSEventLog")   
    thread1.start()

def SaveToResponseService( qsBriefcase : OrchUKRCCQSBriefcase = None, 
    serviceName: str = "", 
    ServiceRequest: str = "", 
    ServiceResponse: str = "", 
    ServiceStartTime : DateTime = None, 
    retrycount :int =0):
        scorereqinputid = qsBriefcase.QSRequest.ScoreRequestInputID
        scorereqID = qsBriefcase.ScoreRequestID
        overallStartTime = qsBriefcase.OverallStartTime
        if(qsBriefcase.OverallEndTime==None):
            overallEndTime = null()
        else:
            overallEndTime = qsBriefcase.OverallEndTime
        correlationID = str(qsBriefcase.CorrelationID)
        if(qsBriefcase.HttpStatusCode==None):
            httpStatusCode = null()
        else:
            httpStatusCode = qsBriefcase.HttpStatusCode
        if(qsBriefcase.CustomStatus==None):
            customStatus = null()
        else:
            customStatus = qsBriefcase.CustomStatus
        try:
            resservice = OrchUKRCCQSResponseService(
                ServiceName = serviceName,
                ServiceRequest = ServiceRequest,
                ServiceResponse = ServiceResponse,
                ServiceStartTime =ServiceStartTime,
                ServiceEndTime = datetime.now(),
                RetryCount = retrycount,
                OverallStartTime = overallStartTime,
                OverallEndTime = overallEndTime,
                CorrelationID = correlationID,
                ScoreRequestID = scorereqID,
                HttpStatusCode = httpStatusCode,
                CustomStatus = customStatus)

            if (scorereqinputid != null):
                resservice.OrchUKRCCQSInputScoreRequestID = scorereqinputid
          
            engine = create_azsql_engine("SAOp")
            session = Session(engine)
            session.add(resservice)
            session.commit()
            qsBriefcase.ResponseServiceID = resservice.OrchUKRCCQSResponseServiceID
        except Exception as e:
            processerror(qsBriefcase.QSRequest, e,"OrchUKRCCQSResponseService")   
        return qsBriefcase

def SaveToResponsePredictor(predictors,     qsBriefcase,     reasonGroupName):
    if (predictors != None):
        session = get_session(engine) #Session(engine1)
        for predictor in predictors:
            ResponsePredictor = OrchUKRCCQSResponsePredictor(
                OrchUKRCCQSInputScoreRequestID = qsBriefcase.ScoreRequestInputID,
                CorrelationID = str(qsBriefcase.CorrelationID),
                PredictorBinValue = predictor.PredictorBinValue,
                PredictorName = predictor.PredictorName,
                PredictorRawValue = predictor.PredictorValue,
                ReasonGroupName = reasonGroupName,
                PredictorId = ModelPredictorCatalog[predictor.PredictorName.replace(" ", "")].value)
            session.add(ResponsePredictor)    
        #Commit all rows at once
        thread1= commitAllSessionChanges(session)  
        thread1.start()
            #thread1 = CommitThread(ResponsePredictor, "OrchUKRCCQSResponsePredictor", qsBriefcase.QSRequest )  
            #thread1.start()

def SaveToResponseReasonMessage( reasons, qsBriefcase):
    if (reasons != None):
        session = get_session(engine) #Session(engine1)
        for reason in reasons:
            ResponseReason = OrchUKRCCQSResponseReasonMessage(
                OrchUKRCCQSInputScoreRequestID = qsBriefcase.ScoreRequestInputID,
                CorrelationID = str(qsBriefcase.CorrelationID),
                MessageColor = reason.MessageColor,
                ReasonGroupName = reason.ReasonGroupName,
                ReasonMessageText = reason.ReasonMessageTxt,              
                PredictorId = null(),
                PredictorName = null(),
                ReasonGroupContribution = null(),
                SAReasonMessageText = null())
            session.add(ResponseReason)    
        #Commit all rows at once
        thread1= commitAllSessionChanges(session)  
        thread1.start()
            #thread1 = CommitThread(ResponseReason, "OrchUKRCCQSResponseReasonMessage", qsBriefcase.QSRequest )   
            #thread1.start()

def SaveToBackingStoreTable(qsRequest, backingStore):
    savingDataTableName = "OrchUKRCCQSBackingStore"
    try:
        session = get_session(engine) #Session(engine1)
        for backingStoreEntrykey, backingStoreEntryvalue in backingStore.items():      
            backingStoreTable = OrchUKRCCQSBackingStore (OrchUKRCCQSInputScoreRequestID = qsRequest.ScoreRequestInputID, 
                                                        KeyField = backingStoreEntrykey, 
                                                        ValueField = backingStoreEntryvalue)
            session.add(backingStoreTable)    
        #Commit all rows at once
        thread1= commitAllSessionChanges(session)  
        thread1.start()
            #thread1 = CommitThread(backingStoreTable, "OrchUKRCCQSBackingStore", qsRequest)   
            #thread1.start()   
    except Exception as e:
        logerror(e)   

# Save the payload to OrchUKRCCQSInputScoreRequest
def SaveToInputRequestJson(json: str, context):
    try:
        json_to_save = OrchUKRCCQSInputScoreRequest(
            InputJsonText = str(json),
            CreateDateTime = datetime.now(),
            Context = context
        )
        engine = create_azsql_engine("SAOp")
        session = Session(engine)
        session.add(json_to_save)
        session.commit()
        session.refresh(json_to_save)
        return json_to_save.OrchUKRCCQSInputScoreRequestID
    except Exception as e:
        processerror(None, e,"OrchUKRCCQSInputScoreRequest")   
            
def SaveToInputPolicy(request : OrchUKRCCQSRequest.OrchUKRCCQSRequest):
    if request.PolicyInput is not null:
        PolicyInput = OrchUKRCCQSInputPolicy(
            OrchUKRCCQSInputScoreRequestID = request.ScoreRequestInputID, 
            PolicyNumber = null() if request.PolicyInput.PolicyNumber=="" else request.PolicyInput.PolicyNumber,
            EffectiveDate = null() if request.PolicyInput.EffectiveDate=="" else request.PolicyInput.EffectiveDate, 
            ExpirationDate = null() if request.PolicyInput.ExpirationDate=="" else request.PolicyInput.ExpirationDate
        )
        thread1 = CommitThread(PolicyInput, "OrchUKRCCQSInputPolicy", request)   
        thread1.start()  

def SaveToInputSubmission(request: OrchUKRCCQSRequest.OrchUKRCCQSRequest):
    if request.SubmissionInput is not null:
        submissionInput = OrchUKRCCQSInputSubmission(
            OrchUKRCCQSInputScoreRequestID = request.ScoreRequestInputID,
            SubmissionNumber = request.SubmissionInput.SubmissionNumber,
            SubmissionCreateDate = request.SubmissionInput.SubmissionCreateDate,
            NatureOfBusiness = null() if request.SubmissionInput.NatureOfBusiness=="" else request.SubmissionInput.NatureOfBusiness,
            PropertyTotalExposureBanded = request.SubmissionInput.PropertyTotalExposureBanded,
            PropertyClaimsHistory5YrsBinary = request.SubmissionInput.PropertyClaimsHistory5YrsBinary
        )
        thread1 = CommitThread(submissionInput, "OrchUKRCCQSInputSubmission", request)   
        thread1.start()  

def SaveToInputClientInfo(request : OrchUKRCCQSRequest.OrchUKRCCQSRequest):
    if request.ClientInfoInput is not null:
        clientInfoInput = OrchUKRCCQSInputClientInfo(
            OrchUKRCCQSInputScoreRequestID = request.ScoreRequestInputID, 
            ClientNumber = request.ClientInfoInput.ClientNumber, 
            ClientName = null() if request.ClientInfoInput.ClientName=="" else request.ClientInfoInput.ClientName,
            ClientLocationHouseNumberStreetName = null() if request.ClientInfoInput.ClientLocationHouseNumberStreetName=="" else request.ClientInfoInput.ClientLocationHouseNumberStreetName,
            ClientLocationLocalityName = null() if request.ClientInfoInput.ClientLocationLocalityName=="" else request.ClientInfoInput.ClientLocationLocalityName,
            ClientLocationTown = null() if request.ClientInfoInput.ClientLocationTown=="" else request.ClientInfoInput.ClientLocationTown,
            ClientLocationPostalCode = null() if request.ClientInfoInput.ClientLocationPostalCode=="" else request.ClientInfoInput.ClientLocationPostalCode,
            ClientLocationCountry = null() if request.ClientInfoInput.ClientLocationCountry=="" else request.ClientInfoInput.ClientLocationCountry
        )
        thread1 = CommitThread(clientInfoInput, "OrchUKRCCQSInputClientInfo", request)   
        thread1.start()  

def SaveToTestResponseInput(request : OrchUKRCCQSRequest.OrchUKRCCQSRequest):
    if request.TestResponsesInput is not null:
        try:
            TestResponse = request.TestResponsesInput
            for item in TestResponse:
                testResponseInput = OrchUKRCCQSInputTestResponse(
                    OrchUKRCCQSInputScoreRequestID = request.ScoreRequestInputID,
                    ServiceContractName = item["ServiceContractName"],
                    ServiceContractTestRequest = item["ServiceContractTestRequest"],
                    ServiceContractTestResponse = item["ServiceContractTestResponse"],
                    ServiceContractsToBeSkipped = item["ServiceContractsToBeSkipped"]
                )
                thread1 = CommitThread(testResponseInput, "OrchUKRCCQSInputTestResponse", request)   
                thread1.start()    
        except Exception as e:
            logerror(e)

def SaveToInput(request : OrchUKRCCQSRequest.OrchUKRCCQSRequest):
    OrchUKRCCQSRequest = request
    try:
        UpdateOrchUKRCCQSInput(request.ScoreRequestInputID, request)
        SaveToInputPolicy(request)
        SaveToInputSubmission(request)        
        SaveToInputClientInfo(request)
        SaveToTestResponseInput(request)
    except Exception as e:
        logerror(e)
    return OrchUKRCCQSRequest

def SaveToOutputScore(qsBriefcase, exhaustiveOutput = "", scoreOutput = ""):
    try:
        if qsBriefcase is not null:
            outputScore = OrchUKRCCQSOutputScore(
                OrchUKRCCQSInputScoreRequestID = qsBriefcase.ScoreRequestInputID, 
                POSTExhaustiveScoreOutputJson = exhaustiveOutput, 
                POSTScoreOutputJson = scoreOutput, 
                CorrelationID = str(qsBriefcase.CorrelationID)
            )
            thread1 = CommitThread(outputScore, "OrchUKRCCQSOutputScore", qsBriefcase.QSRequest)   
            thread1.start()     
    except Exception as e:
        logerror(e)

def SaveToResponseScore(qsBriefcase):
    try:
        if qsBriefcase is not null:
            responseScore = OrchUKRCCQSResponseScore(
                OrchUKRCCQSInputScoreRequestID = qsBriefcase.ScoreRequestInputID,               
                CorrelationID = str(qsBriefcase.CorrelationID)
            )

            responseScore.OverallScore = qsBriefcase.OverallScore
            responseScore.ELScore = qsBriefcase.ELScore  
            responseScore.GLScore = qsBriefcase.GLScore  
            responseScore.PropScore = qsBriefcase.PropScore  
            responseScore.SubmissionNumber = qsBriefcase.SubmissionNumber  
            if (len(qsBriefcase.Errors) > 0):
                responseScore.Status = "Completed with Errors"
            elif (len(qsBriefcase.Warnings) > 0):
                responseScore.Status = "Completed with Warnings"
            else:
                responseScore.Status = "Completed"
            thread1 = CommitThread(responseScore, "OrchUKRCCQSResponseScore", qsBriefcase.QSRequest)   
            thread1.start()  
    except Exception as e:
        logerror(e)

def UpdateOrchUKRCCQSInput(
    OrchUKRCCQSInputScoreRequestID: int,
    request: OrchUKRCCQSRequest
    ):
    try:
        engine = create_azsql_engine("SAOp")
        session = Session(engine)
        update_obj = session.query(OrchUKRCCQSInputScoreRequest).get(OrchUKRCCQSInputScoreRequestID)
        update_obj.IsBulk = request.ScoreRequestInput.IsBulk
        update_obj.TransactionType = request.ScoreRequestInput.TransactionType
        update_obj.TransactionTimeStamp = request.ScoreRequestInput.TransactionTimeStamp
        update_obj.ScoreRequestID = request.ScoreRequestInput.ScoreRequestID
        update_obj.SourceSystem = request.ScoreRequestInput.SourceSystem    
        update_obj.SourceSystemAction = request.ScoreRequestInput.SourceSystemAction
        update_obj.ProductType = request.ScoreRequestInput.ProductType
        update_obj.CorrelationID = request.CorrelationID
        session.commit()
    except Exception as e:
       processerror(request, e,"OrchUKRCCQSInputScoreRequest")  

def SaveToDNBOutputService(dnBData, qsBriefcase):
    try:        
        if dnBData!=None:            
            dnBData.OrchUKRCCQSInputScoreRequestID = qsBriefcase.ScoreRequestInputID               
            dnBData.CorrelationID = str(qsBriefcase.CorrelationID)
            dnBData.AccountName = qsBriefcase.QSRequest.ClientInfoInput.ClientName
            dnBData.StreetAddress1 = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationHouseNumberStreetName
            dnBData.StreetAddress2 = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationLocalityName
            dnBData.City = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationTown
            dnBData.ZipCode = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationPostalCode
            dnBData.Country = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationCountry
            dnBData.Sourcesystem = qsBriefcase.QSRequest.ScoreRequestInput.SourceSystem
            thread2 = CommitThread(dnBData, "OrchUKRCCQSOutputDnBService", qsBriefcase.QSRequest)   
            thread2.start()
    except Exception as e:
        logerror(e)
