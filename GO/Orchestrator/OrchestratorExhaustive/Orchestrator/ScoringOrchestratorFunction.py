import os
import json
import logging
import http.client
import azure.functions as fx
import requests

from email import header
from datetime import date
from wsgiref import headers
from dateutil import parser
from datetime import datetime
from typing import List
from py_linq import Enumerable
from xmlrpc.client import DateTime
from shared_code import Constants
from ..Model.OrchUKRCCQSBriefcase import OrchUKRCCQSBriefcase
from ..Model.OrchUKRCCQSBriefcase import VariableInput
from ..Model.Metadata.OrchestratorSummary import OrchestratorSummary
from ..Model.Metadata.ServiceContract import ServiceContract
from ..Model.Entities.OrchUKRCCQSOutputDnBService import OrchUKRCCQSOutputDnBService
from ..Model.OrchUKRCCQSResponseExhaustive import OrchUKRCCQSResponseExhaustiveEncoder
from ...shared_code.ObjectSerializer import ObjectSerializer
from ..Data.Dao import *
from ..Data.Repository import *
from FE import call_FE

def RunActivity(qsBriefcase : OrchUKRCCQSBriefcase,orchestratorSummary : OrchestratorSummary,req_body : str, correlationID : str) :
    #logging.info("ScoringOrchestratorService.Orchestrate started")
    backingStore = {}
    qsRequest = qsBriefcase.AllResults["qsRequest"]
    #initialize SKIPs
    for sc in orchestratorSummary.ServiceContracts:
        backingStore[sc.ServiceContractName.lower() + "skip"] = "0"
    #Save to event log
    #jsonData = json.dumps(qsBriefcase.AllResults["qsRequest"])
    AddToBackingStore(backingStore, "", req_body)
    AddToBackingStore(backingStore, "CorrelationID",str(correlationID))
    
    #to make the payload case insensitive update the backing store keys to lower case
    backingStore = {k.lower():v for k,v in backingStore.items()}

    for sequencer in orchestratorSummary.Sequencers:
        #1.Root level object
        root = {}
        #dictionary for all objects
        jsonAllObjectsDictionary =  {}
        #2. Search child service contract in OrchestratorSummary.ServiceContracts
        ServiceToCall : ServiceContract = Enumerable(orchestratorSummary.ServiceContracts).where(lambda x: x.ServiceContractId == sequencer.ChildServiceContract).first_or_default()
        #2.1 Check if testResponse is present for this service 
        qsBriefcase.Stage = ServiceToCall.ServiceContractName
        itr : InputTestResponse = Enumerable(qsRequest.TestResponsesInput).where(lambda c : c["ServiceContractName"] == ServiceToCall.ServiceContractName).first_or_default()
        # for itr in qsRequest.TestResponsesInput:
        #     if(itr.ServiceContractName == ServiceToCall.ServiceContractName):
        #         break

        ServiceStartTime = datetime.now()
        ProcessTestResponse(qsBriefcase, itr, ServiceToCall, backingStore, ServiceStartTime)
        #2.2 Check if service call needs to be skippedskipService
        skipService = backingStore[ServiceToCall.ServiceContractName.lower() + "skip"]
        if (skipService=="1"):
            qsBriefcase.Status = "Skipped"
            qsBriefcase.httpstatus = "NA"
            SaveToEventLog(qsRequest.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= str(qsRequest.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
            SaveToResponseService(qsBriefcase, ServiceToCall.ServiceContractName, "Service Call Skipped", "Service Call Skipped", ServiceStartTime, 0)
        else:
            jsonCurrentLevelObjectDictionary ={} #dictionary for only first level Array Objects Index
            arrayJObjects = {}
            for input in ServiceToCall.ServiceContractInputs:               
                #Prepare input json
                if("index1" in input.ServiceContractInputParameterDestination or 
                    "index2" in input.ServiceContractInputParameterDestination) :
                       arrayJObjects = createservicecontractinput_forlist(input, input.ServiceContractInputParameterDestination, input.ServiceContractInputParameterSource, jsonCurrentLevelObjectDictionary, backingStore, 1, qsBriefcase)
                                    
                else:
                    objects = input.ServiceContractInputParameterDestination.split('.')
                    defaultValue = input.ServiceContractInputParameterDefaultValue
                    if(len(objects)==1):
                        createservicecontractinput_forplainfield(defaultValue, root, input, backingStore, qsBriefcase)
                    elif(len(objects)==2):    
                        jsonObject = None
                        if (objects[0] in jsonAllObjectsDictionary):
                            jsonObject = jsonAllObjectsDictionary[objects[0]] #get if object is already created
                        else:
                            jsonObject = {} #create new if not already created
                            jsonAllObjectsDictionary[objects[0]]= jsonObject
                            root[objects[0]]= jsonObject
                        createservicecontractinput_forplainfield(defaultValue, jsonObject, input, backingStore, qsBriefcase)
                    elif(len(objects)==3):
                       logging.info("TODO len(objects)==3 Prepare input json Ended") 
            #update array input data
            if (arrayJObjects != None and len(arrayJObjects)>0):
                firstkey = list(arrayJObjects.items())[0][0]
                firstvalue = list(arrayJObjects.items())[0][1]
                if (firstkey not in root):
                    root[firstkey]= firstvalue
                else:
                    #update the link
                    previousValue = list(root.items())[firstkey][0]
                    previousValue.extend(firstvalue)
                    root[firstkey] = previousValue
            
            
            qsBriefcase.Stage = ServiceToCall.ServiceContractName
            qsBriefcase.Status = "CallingService"
            inputPayload , response = CallService(ServiceToCall, root, qsRequest, qsBriefcase,backingStore)
            outputPayload= json.dumps(response)
            logging.info("Service Call finished for " + ServiceToCall.ServiceContractName)
            if((response!=None) & (qsBriefcase.HttpStatusCode == 200)):
                #3. add result of service to breafcase
                qsBriefcase.AllResults[ServiceToCall.ServiceContractName] = response
                qsBriefcase.ServiceRequests[ServiceToCall.ServiceContractName] = inputPayload
                #4. save the response in backingStore based on ServiceContractOutputParameterDestination
                SaveResponseInBackingStoreForServiceContractOutputParameterDestination(qsBriefcase, ServiceToCall, backingStore, response)
                #5. check custom status
                customestatus = GetValue(backingStore, ServiceToCall.ServiceContractName.lower() + "status")
                if (customestatus != None):
                    qsBriefcase.CustomStatus = customestatus
                #6. Save in ResponseService
                SaveToResponseService(qsBriefcase, ServiceToCall.ServiceContractName, inputPayload, outputPayload, ServiceStartTime, 0)
            else:
                #3.add result of service to breafcase
                if (response != None and response!=""):
                    try:                   
                        qsBriefcase.AllResults[ServiceToCall.ServiceContractName + "ErrorOutput"] = response
                        #4. save the response in backingStore based on ServiceContractOutputParameterDestination
                        SaveResponseInBackingStoreForServiceContractOutputParameterDestination(qsBriefcase, ServiceToCall, backingStore, response)
                    
                    except Exception as e:
                        qsBriefcase.AllResults[ServiceToCall.ServiceContractName + "ErrorOutput"] = response
                qsBriefcase.Status = "Failed"
                #Save the issue with Calling Service
                errCode = "ServiceContractCallError"
                errDescription = ServiceToCall.ServiceContractName + " Failed"
                errModule = ServiceToCall.ServiceContractName
                qsBriefcase.Errors.append(CodeDescModule(Code= errCode, Description = errDescription, Module = errModule))
                SaveToEventLog(qsBriefcase.ScoreRequestInputID, errModule, Constants.Char_Status_Failed, errCode, ErrorDescription= errDescription, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
                #Save in ResponseService
                SaveToResponseService(qsBriefcase, ServiceToCall.ServiceContractName, inputPayload, outputPayload, ServiceStartTime, 0)

    qsBriefcase.OverallStartTime = datetime.now()
    #save predictors and reason messages
    SaveReasons(backingStore, qsBriefcase)
    #save backing store in a table for debugging purposes
    SaveBackingStoreForDebuggingPurposes = os.getenv("SaveBackingStoreForDebuggingPurposes")
    if (SaveBackingStoreForDebuggingPurposes != None and SaveBackingStoreForDebuggingPurposes=="Yes"):
        SaveToBackingStoreTable(qsRequest, backingStore)

    qsBriefcase.Stage = "RequestStage_QSRequestCompleted"
    qsBriefcase.Status = "Completed"
    OverallScore = GetValue(backingStore, "MODELOVERALL_BUCKET")
    if (OverallScore != None):
        qsBriefcase.OverallScore = OverallScore
    ELScore = GetValue(backingStore, "MODELEL_BUCKET")
    if (ELScore != None):
        qsBriefcase.ELScore = ELScore
    GLScore = GetValue(backingStore, "MODELGL_BUCKET")
    if (GLScore != None):
        qsBriefcase.GLScore = GLScore
    PropScore = GetValue(backingStore, "MODELPROP_BUCKET")
    if (PropScore != None):
        qsBriefcase.PropScore = PropScore
    SaveToEventLog(qsRequest.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID=str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
    logging.info("Orchestration finished ")
    qsBriefcase.OverallEndTime = datetime.now()
    return qsBriefcase

#data save methods
def SaveReasons(backingStore, qsBriefcase):
    reasons = []
    maxIndexReasonMessages = getMaxIndex(backingStore, "reasonoutput")
    for i in range(0, maxIndexReasonMessages):
        MessageColor = GetValue(backingStore, "reasonoutput[" + str(i) + "].messagecolor") 
        ReasonMessageTxt = GetValue(backingStore, "reasonoutput[" + str(i) + "].reasonmessagetxt")
        ReasonGroupName = GetValue(backingStore, "reasonoutput[" + str(i) + "].reasongroupname")
        ro = ReasonOutput.ReasonOutput(MessageColor,ReasonMessageTxt,ReasonGroupName)
        reasons.append(ro)
        SavePredictors(backingStore, qsBriefcase, ro, i)

    qsBriefcase.ReasonOutputs = reasons
    SaveToResponseReasonMessage(reasons, qsBriefcase)

def SavePredictors(backingStore, qsBriefcase, ro, i):
    predictors = []
    maxIndexPredictors = getMaxIndex(backingStore, "reasonoutput[" + str(i) + "].predictoroutput")
    for j in range(0, maxIndexPredictors): 
        PredictorValue = GetValue(backingStore, "reasonoutput[" + str(i) + "].predictoroutput[" + str(j) + "].predictorvalue")
        #PredictorBinValue = GetValue(backingStore, "reasonoutput[" + str(i) + "].predictoroutput[" + str(j) + "].predictorbinvalue")
        PredictorName = GetValue(backingStore, "reasonoutput[" + str(i) + "].predictoroutput[" + str(j) + "].predictorname")
        #po = PredictorOutput.PredictorOutput(PredictorValue,PredictorBinValue,PredictorName)
        po = PredictorOutput.PredictorOutput(PredictorValue,None,PredictorName)
        predictors.append(po)

    ro.PredictorOutputs = predictors
    SaveToResponsePredictor(predictors, qsBriefcase, ro.ReasonGroupName)

#dynamic payload creation methods
def createservicecontractinput_forlist(input,inputServiceContractInputParameterDestination, inputServiceContractInputParameterSource, jsonCurrentLevelObjectDictionary, backingStore, level, qsBriefcase):
    #logging.info("CreateServiceContractInputForList")
    #if input parameter is an array
    inputParameterDestinationSplits = inputServiceContractInputParameterDestination.split(".")
    inputParameterSourceSplits = inputServiceContractInputParameterSource.split(".")
    keytoaddtoRoot = inputParameterDestinationSplits[0].replace("[index" + str(level) + "]", "")
    defaultValue = input.ServiceContractInputParameterDefaultValue
    if (len(inputParameterDestinationSplits) == 2):
        jsonArrayObject = []
        if (("index" + str(level)) in inputParameterDestinationSplits[0]):
            maxIndexForCurrentLevel = getMaxIndex(backingStore, inputParameterSourceSplits[0].replace("[index" + str(level) + "]", ""))
            for i in range(0, maxIndexForCurrentLevel):
                jsonObject = {}
                jArrayKey = inputParameterDestinationSplits[0].replace("[index" + str(level) + "]", "[" + str(i) + "]")
                jsonObject = IsJsonObjectAlreadyPresentInDictionary(jsonCurrentLevelObjectDictionary, jArrayKey)
                if (("index" + (str(level + 1)))  not in inputParameterSourceSplits[1]):
                    inputParameterSourceName = inputServiceContractInputParameterSource.replace("[index" + str(level) + "]", "[" + str(i) + "]")
                    inputParameterDestinationName = inputParameterDestinationSplits[1]
                    if (defaultValue==None or defaultValue==""):
                        #jsonObject.Add(inputParameterDestinationName, GetValue(backingStore, inputParameterSourceName))
                        UpdatejsonObject(input, backingStore, inputParameterSourceName, jsonObject, inputParameterDestinationName, qsBriefcase)                    
                    elif (input.ServiceContractInputParameterSource.lower() =="config"):
                        configValue = os.getenv(defaultValue)
                        jsonObject[input.ServiceContractInputParameterName]=configValue
                    elif (defaultValue.lower() == "(blank)"):
                        jsonObject[input.ServiceContractInputParameterName]= ""
                    else:
                        jsonObject[input.ServiceContractInputParameterName]=defaultValue

                    jsonCurrentLevelObjectDictionary[jArrayKey] = jsonObject
                    jsonArrayObject.append(jsonObject)
                
                else:
                    #pure array ex imagetext in OCR output
                    maxIndexForCurrentLevelPureArray = getMaxIndex(backingStore, inputParameterSourceSplits[0].replace("[index" + str(level) + "]", "[" + str(i) + "].") + inputParameterSourceSplits[1].replace("[index" + (level + 1) + "]", ""))
                    jsonArrayObject1 = []
                    inputParameterDestinationName = inputParameterDestinationSplits[1].replace("[index" + (level + 1) + "]", "")
                    for k in range(0, maxIndexForCurrentLevelPureArray):
                        inputParameterSourceName = inputParameterSourceSplits[0].replace("[index" + str(level) + "]", "[" + str(i) + "].") + inputParameterSourceSplits[1].replace("[index" + (level + 1) + "]", "[" + str(k) + "]")

                        if (defaultValue==None or defaultValue==""):
                            UpdatejsonObject(input, backingStore, inputParameterSourceName, jsonObject, inputParameterDestinationName, qsBriefcase)
                        elif (input.ServiceContractInputParameterSource.lower() =="config"):
                            configValue = os.getenv(defaultValue)
                            jsonObject[input.ServiceContractInputParameterName]=configValue
                        elif (defaultValue.lower() == "(BLANK)"):
                            jsonObject[input.ServiceContractInputParameterName]=""
                        else:
                            jsonObject[input.ServiceContractInputParameterName]=defaultValue
                        
                    jsonObject[inputParameterDestinationName] = jsonArrayObject1
                    jsonCurrentLevelObjectDictionary[jArrayKey] = jsonObject
                    jsonArrayObject.append(jsonObject)
        #recursive function exit criteria
        toReturn = {}
        toReturn[keytoaddtoRoot] = jsonArrayObject
        return toReturn          
    #call the same function recursevely
    jsonnextLevelObjectDictionary = {} #dictionary for only first level Array Objects Index
    parent = {}
    childJObject = createservicecontractinput_forlist(input, inputParameterDestinationSplits[1], inputParameterSourceSplits[1], jsonnextLevelObjectDictionary, backingStore, level + 1, qsBriefcase)

    if (childJObject.key not in parent):
        parent.Add(childJObject.key, childJObject.value)    
    else:
        #update the link
        previousValue = parent[childJObject.key]
        previousValue[len(previousValue+1)] = childJObject
        parent[childJObject.key] = previousValue    

    return childJObject   

def IsJsonObjectAlreadyPresentInDictionary(jsonCurrentLevelObjectDictionary, jArrayKey):
    #logging.info("IsJsonObjectAlreadyPresentInDictionary")
    JObject = None
    if (jArrayKey in jsonCurrentLevelObjectDictionary):
         jsonObject = jsonCurrentLevelObjectDictionary[jArrayKey] #get if JArray is already created
    else:
        jsonObject = {} #create new if not already created
        jsonCurrentLevelObjectDictionary[jArrayKey]= jsonObject
    return jsonObject

def createservicecontractinput_forplainfield(defaultValue, root, input, backingStore, qsBriefcase):
    #logging.info("CreateServiceContractInputForPlainField")
    if (defaultValue==""):
        UpdatejsonObject(input, backingStore, input.ServiceContractInputParameterSource, root, input.ServiceContractInputParameterDestination, qsBriefcase)
    elif (input.ServiceContractInputParameterSource == "Config"):
        configValue = os.getenv(defaultValue)
        root[input.ServiceContractInputParameterName]= configValue
    elif (input.ServiceContractInputParameterSource=="Method"):
        dynamic_func = globals()[defaultValue]
        methodReturnValue = dynamic_func(qsBriefcase.QSRequest)
        if (methodReturnValue != None):
            root[input.ServiceContractInputParameterName]= methodReturnValue
        else:
            root[input.ServiceContractInputParameterName]= ""
    elif (defaultValue=="(BLANK)"):
        root[input.ServiceContractInputParameterName]= ""    
    else:
        root[input.ServiceContractInputParameterName]= defaultValue

def UpdatejsonObject(input, backingStore, inputParameterSourceName, jsonObject, inputParameterDestinationName, qsBriefcase):
    #logging.info("UpdatejsonObject" + inputParameterSourceName)
    value = GetValue(backingStore, inputParameterSourceName.lower())
    if (":" in input.ServiceContractInputParameterDataType):    
        try:        
            #it has format defined          
            if(value == None):
                dateValue = parser.Parse(Constants.defaultDate) 
            else:
                dateValue = value
            jsonObject[inputParameterDestinationName] = dateValue        
        except:        
            jsonObject[inputParameterDestinationName] = None
            #handle exception when value can not be converted to date
            errorMessage = "Date Conversion Error for " + inputParameterDestinationName + " for " + qsBriefcase.Stage
            logging.info(errorMessage)
            warning = {"Code" : Constants.DataConversionError, "Description": errorMessage}
            if (input.ServiceContractInputParameterMandatoryRule=="true"):
                qsBriefcase.Warnings.Add(warning)
            SaveToEventLog(qsBriefcase.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID, WarningCode= warning.Code, WarningDescription= warning.Description)
    elif (input.ServiceContractInputParameterDataType.lower()=="int"):
    
        try:
            if (value != None and value!=""): 
                intValue = int(value)
                jsonObject[inputParameterDestinationName] = intValue
            else:
                jsonObject[inputParameterDestinationName] = None     
        except:        
            jsonObject[inputParameterDestinationName] = None
            #handle exception when value can not be converted to int
            errorMessage = "Int Conversion Error for " + inputParameterDestinationName + " for " + qsBriefcase.Stage
            logging.info(errorMessage)
            warning = {"Code" : Constants.DataConversionError, "Description": errorMessage}
            if (input.ServiceContractInputParameterMandatoryRule=="true"):
                qsBriefcase.Warnings.Add(warning)
            SaveToEventLog(qsBriefcase.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID, WarningCode= warning.Code, WarningDescription= warning.Description)
    elif (input.ServiceContractInputParameterDataType.lower()=="double"):
    
        try:
            if (value != None and value!=""):    
                floatValue = float(value)   
                jsonObject[inputParameterDestinationName] = floatValue
            else:
                jsonObject[inputParameterDestinationName] = None          
        except:
        
            jsonObject[inputParameterDestinationName] = None
            #handle exception when value can not be converted to double
            errorMessage = "Double Conversion Error for " + inputParameterDestinationName + " for " + qsBriefcase.Stage
            logging.info(errorMessage)
            warning = {"Code" : Constants.DataConversionError, "Description": errorMessage}
            if (input.ServiceContractInputParameterMandatoryRule=="true"):
                qsBriefcase.Warnings.Add(warning)
            SaveToEventLog(qsBriefcase.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID, WarningCode= warning.Code, WarningDescription= warning.Description)
    else:
    
        if (value != None):        
            jsonObject[inputParameterDestinationName] = str(value)        
        else:
            jsonObject[inputParameterDestinationName] = None
            errorMessage = "Value is None for " + inputParameterDestinationName + " for " + qsBriefcase.Stage
            logging.info(errorMessage) #, true)
            warning = {"Code" : Constants.DataConversionError, "Description": errorMessage}
            if (input.ServiceContractInputParameterMandatoryRule=="true"):
                qsBriefcase.Warnings.Add(warning)
            SaveToEventLog(qsBriefcase.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= qsBriefcase.CorrelationID, ScoreRequestID= qsBriefcase.ScoreRequestID, WarningCode= warning.Code, WarningDescription= warning.Description)

def SaveResponseInBackingStoreForServiceContractOutputParameterDestination(qsBriefcase, ServiceToCall, backingStore, response):
            
            #remove first and last [ to prevent following error
            if(type(response)==list):
                response = response[0]
            backingStoreIntrim = {}
            AddToBackingStore(backingStoreIntrim, "", response)
            for output in ServiceToCall.ServiceContractOutputs:
                if("index1" in output.ServiceContractOutputParameterName):
                    #todo pending multilevel array
                    endSearchPosition = output.ServiceContractOutputParameterName.index("[index1]")
                    keyToSearch = output.ServiceContractOutputParameterName[0:endSearchPosition].replace("[index1]", "")
                    maxIndex1 = getMaxIndex(backingStoreIntrim, keyToSearch)
                    for i in range(0, maxIndex1): 
                        if ("index2" in output.ServiceContractOutputParameterName):
                            endSearchPosition2 = output.ServiceContractOutputParameterName.index("[index2]")
                            keyToSearch2 = keyToSearch + "[" + str(i) + "]" + output.ServiceContractOutputParameterName[endSearchPosition + 8:endSearchPosition2].replace("[index2]", "")
                            maxIndex2 = getMaxIndex(backingStoreIntrim, keyToSearch2)
                            for k in range(0, maxIndex2):
                                SetValue(backingStoreIntrim, output.ServiceContractOutputParameterName.replace("[index1]", "[" + str(i) + "]").replace("[index2]", "[" + str(k) + "]"), output.ServiceContractOutputParameterDestination.replace("[index1]", "[" + str(i) + "]").replace("[index2]", "[" + str(k) + "]"))
                        
                        else:
                            SetValue(backingStoreIntrim, output.ServiceContractOutputParameterName.replace("[index1]", "[" + str(i) + "]"), output.ServiceContractOutputParameterDestination.replace("[index1]", "[" + str(i) + "]"))
                        
                else:
                    SetValue(backingStoreIntrim, output.ServiceContractOutputParameterName, output.ServiceContractOutputParameterDestination)
                
            for Key1, Value1 in backingStoreIntrim.items():
                try:
                    backingStore[Key1] = Value1
                except Exception as e:
                    logging.info(str(e))
                    warning = CodeDesc ( Code = Constants.DataConversionError, Description = str(e) )
                    qsBriefcase.Warnings.append(warning)
                    SaveToEventLog(qsBriefcase.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID, WarningCode=warning.Code, WarningDescription= warning.Description)
                   
#backing store methods
def AddToBackingStore(backingStore, prefix, value):
    #for key value pair
    if (type(value) is dict):
        for Key1, Value1 in value.items():
            AddToBackingStore(backingStore, MakePropertyKey(prefix, Key1), Value1)
        return
    #for arrays
    if (type(value) is list):
        urls = value
        for j in range(0, len(urls)):
            AddToBackingStore(backingStore, MakeArrayKey(prefix, j), urls[j])
        return    
    #for primitive
    backingStore[prefix.lower()]=value

def MakeArrayKey(prefix, index):
    return prefix + "[" + str(index) + "]"

def MakePropertyKey(prefix, propertyName):
    if(prefix==""):
        return propertyName
    else:
        return prefix + "." + propertyName

def getMaxIndex(backingStore, keyToSearch):
    maxIndex = 0
    keyToSearch = keyToSearch.lower()
    try:
        #for arrays
        for value in backingStore.keys():
            if (keyToSearch in value) and ("[" in value):
                startSearchPosition = value.index(keyToSearch) + len(keyToSearch) + 1
                if (startSearchPosition == len(value) + 1):
                    return 0
                lentghofIndex = value.index("]", startSearchPosition) - startSearchPosition
                if (lentghofIndex > 0):
                    index = int(value[startSearchPosition:startSearchPosition +lentghofIndex])
                    if (index >= maxIndex):
                        maxIndex = index+1
                
    except:
        #do nothing
        logging.info("Error in getMaxIndex")
    return maxIndex

def GetValue(backingStore, key):
    value = None
    if (key.lower() in backingStore):
        value = backingStore.get(key.lower())
    if (value == None):
        return ""
    return value

def SetValue(backingStore, key, newkey):
    value = None
    if (key.lower() in backingStore):    
        value = backingStore.get(key.lower())
        #remove old key
        backingStore.pop(key.lower())
        #add new key with same value
        backingStore[newkey.lower()]= value
        return 1
    return 0

#For calling service
def CallService(serviceToCall, root, qsRequest, qsBriefcase, backingStore):
    logging.info("CallService") 
    ServiceStartTime = datetime.now()
    response = None
    inputPayload = json.dumps(root)
    outputPayload = None
    httpstatus =""
    if (serviceToCall.ServiceKeyType.lower() == "posturl"):
        serviceKey = os.getenv(serviceToCall.ServiceKey)
        logging.info(serviceKey)
        if (serviceToCall.SecurityTokenKey != None and serviceToCall.SecurityTokenKey != ""):  
            modelpayloadlist =[] 
            modelpayloadlist.append(root)                         
            inputPayload = json.dumps(modelpayloadlist)
            logging.info(inputPayload)
            modelToken = os.getenv(serviceToCall.SecurityTokenKey)
            SaveToEventLog(qsRequest.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, ErrorStackTrace= inputPayload, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
            response, httpstatus = CallPostServiceWithToken(qsRequest,serviceToCall.ServiceContractName, serviceKey, modelToken, modelpayloadlist)
        else:
            logging.info(inputPayload)
            SaveToEventLog(qsRequest.ScoreRequestInputID, qsBriefcase.Stage, qsBriefcase.Status, ErrorStackTrace= inputPayload, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
            response, httpstatus = CallPostService(qsRequest,serviceToCall.ServiceContractName,serviceKey, root)
    elif (serviceToCall.ServiceKeyType.lower() == "method"):
        parameters = []
        parameters.append(inputPayload)
        parameters.append(backingStore)
        parameters.append(qsBriefcase)
        parameters.append(serviceToCall)
        methodReturnValue = globals()[serviceToCall.ServiceKey]
        if (methodReturnValue != None):
            response = methodReturnValue(parameters) 
            httpstatus = 200
        else:
            httpstatus = 500
    ServiceEndTime = datetime.now()
    
    qsBriefcase.HttpStatusCode = httpstatus
    return inputPayload, response #, datetime.now(), inputPayload      
 
def CallPostServiceWithToken(qsRequest, serviceContractName, serviceKey, modelToken, inputPayload):
    try:
        logging.info("CallPostServiceWithToken")
        HEADERS = {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + modelToken
                }
        URL = serviceKey
    
        # defining a params dict for the parameters to be sent to the API
        PARAMS = inputPayload
        
        # sending get request and saving the response as response object
        r = requests.post(url = URL, json = PARAMS, headers = HEADERS)
        
        # extracting data in json format
        data = r.json()
        httpstatus = r.status_code
        return data, httpstatus
    except Exception as e:
        logging.info('ServiceCallError' + serviceContractName)
        if(qsRequest!=None):   
            errorDescription = "Error in calling service " + serviceContractName + " " + str("" if r else r.status_code) + " " + str(e)
            SaveToEventLog(qsRequest.ScoreRequestInputID, "RequestStage_ServiceCall", "Status_Failed", "ServiceCallError", "ScoringOrchestratorFunction.CallPostService", errorDescription, CorrelationID= str(qsRequest.CorrelationID), ScoreRequestID= qsRequest.ScoreRequestInput.ScoreRequestID)
            qsRequest.Errors.append(CodeDesc (Code = "ServiceCallError", Description = errorDescription))
            data ={}
            data["error_code"] = "ServiceCallError"
            data["message"] = "InternalServerError"
            return data, r.status_code


def CallPostService(qsRequest, serviceContractName, serviceKey, inputPayload):
    try:
        logging.info("CallPostService")  
        URL = serviceKey
    
        # defining a params dict for the parameters to be sent to the API
        PARAMS = inputPayload
        
        # sending get request and saving the response as response object
        r = requests.post(url = URL, json = PARAMS)
        
        # extracting data in json format
        data = r.json()
        httpstatus = r.status_code
        return data, httpstatus
    except Exception as e:
        logging.info('ServiceCallError' + serviceContractName)
        if(qsRequest!=None):   
            errorDescription = "Error in calling service " + serviceContractName + " " + str(r.status_code) + " " + str(e)
            SaveToEventLog(qsRequest.ScoreRequestInputID, "RequestStage_ServiceCall", "Status_Failed", "ServiceCallError", "ScoringOrchestratorFunction.CallPostService", errorDescription, CorrelationID= str(qsRequest.CorrelationID), ScoreRequestID= qsRequest.ScoreRequestInput.ScoreRequestID)
            qsRequest.Errors.append(CodeDesc (Code = "ServiceCallError", Description = errorDescription))
            data ={}
            data["error_code"] = "ServiceCallError"
            data["message"] = "InternalServerError"
            return data, r.status_code

#For testResponses
def ProcessTestResponse(qsBriefcase, itr, ServiceToCall, backingStore, ServiceStartTime):
    if (itr != None):
        qsBriefcase.Status = "UsingTestResponse"

        #3. Add result of service to breafcase
        outputPayload = itr["ServiceContractTestResponse"]
        inputPayload = itr["ServiceContractTestRequest"]

        qsBriefcase.AllResults[ServiceToCall.ServiceContractName] = json.loads(outputPayload)
        qsBriefcase.ServiceRequests[ServiceToCall.ServiceContractName] = inputPayload

        #4. Save the response in backingStore based on ServiceContractOutputParameterDestination
        SaveResponseInBackingStoreForServiceContractOutputParameterDestination(qsBriefcase, ServiceToCall, backingStore, json.loads(outputPayload))

        #5. check custom status
        customestatus = GetValue(backingStore, ServiceToCall.ServiceContractName.lower() + "status")

        if (customestatus != None):
            qsBriefcase.CustomStatus = customestatus
        #6. Save in ResponseService
        SaveToResponseService(qsBriefcase, ServiceToCall.ServiceContractName, inputPayload, outputPayload , ServiceStartTime, 0)

        #skip service for which the response is passed
        ServiceContractsToBeSkippedSplits = itr["ServiceContractsToBeSkipped"].split(",")
        for i in range(0, len(ServiceContractsToBeSkippedSplits)):
            backingStore[ServiceContractsToBeSkippedSplits[i].lower() + "skip"] = "1"


def CustomMethod_NLPPreProcessing(parameters):
    inputPayload = parameters[0]
    backingStore = parameters[1]
    qsBriefcase = parameters[2]
    serviceToCall = parameters[3]
    logging.info("CustomMethod_NLPPreProcessing") 
    methodResponse = ""
    #Call method to create VARIABLE_LISTNLP array to feed as input for VARIABLE_LIST
    try:
        variableInputNLP ={}
        variableInputList = []
        variableInputList.append(VariableInput (variableName = "PRODUCTTYPE", variableValue = qsBriefcase.QSRequest.ScoreRequestInput.ProductType))
        variableInputList.append(VariableInput (variableName = "BUSINESSDESCRIPTION", variableValue = qsBriefcase.QSRequest.SubmissionInput.NatureOfBusiness))
        variableInputNLP["VariableInputNLP"] = variableInputList
        qsBriefcase.VariableInputNLP = variableInputNLP
        #add VariableInputNLP to backing store
        jsonData = "{\"VariableInputNLP\":" + json.dumps([o.__dict__ for o in variableInputList]) + "}"
        AddToBackingStore(backingStore, "", json.loads(jsonData))
    except Exception as e:
        error = CodeDescModule() 
        error.Code = "NLPPreProcessing Error"
        error.Description = e.Message
        error.Module = "NLPPreProcessing"
        qsBriefcase.Errors.append(error)
        SaveToEventLog(qsBriefcase.ScoreRequestInputID, "CustomMethod_NLPPreProcessing", "Status_Failed", error.Code, error.Module, error.Description, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
        return "{\"NLPPreProcessingResponse\":\" Error \" }"
    methodResponse = "{\"NLPPreProcessingResponse\":\" OK \" }"
    return methodResponse

def CustomMethod_FetchDNBDataToReuse(parameters):
    inputPayload = parameters[0]
    backingStore = parameters[1]
    qsBriefcase = parameters[2]
    serviceToCall = parameters[3]
    logging.info("CustomMethod_FetchDNBDataToReuse") 
    REUSEDUNANDBRADSTREET = False
    methodResponse = ""
    #Call method to get exising dnb data 
    #check if the data found then add the result to backing store
    #otherwise add the location to NewClientsInput collection to go to DNB
    #get previous dnb data
    try:
        #Fetch old records based on submissionid
        oldDnBData = GetOldDnBData(qsBriefcase.QSRequest.ClientInfoInput, qsBriefcase.QSRequest)
        logging.info("oldDnBData searched") 
        if (oldDnBData!=None):
            logging.info("oldDnBData found") 
            REUSEDUNANDBRADSTREET = True
            qsBriefcase.ReusedDNBData = oldDnBData
            #old dnb data but exposure will be new
            oldDnBData.DNBServiceResponse = "Reuse of Old data"
            oldDnBData.SEUKConvBranchInputScoreRequestID = qsBriefcase.ScoreRequestInputID
            # Store the DnB Output data on reuse of DnB data not just when we call D&B.  Mark it as reuse somehow
            SaveToDNBOutputService(oldDnBData, qsBriefcase)        
        else:
            logging.info("oldDnBData not found") 
            qsBriefcase.NewClientInput = qsBriefcase.QSRequest.ClientInfoInput
        
    except Exception as e:
        logging.info("oldDnBData found error") 
        dataSaveErrors =[]
        for	x in range(0,len(e.args)):
            create_errors_collection("DataSaveError", e.args[x], dataSaveErrors)
        for	dataSaveError in dataSaveErrors: 
            logging.info(dataSaveError)
        error = CodeDescModule("DNB Error",str(e),"FetchDNBDataToReuse")         
        qsBriefcase.Errors.append(error)
        SaveToEventLog(qsBriefcase.ScoreRequestInputID, "CustomMethod_FetchDNBDataToReuse", "Status_Failed", error.Code, error.Module, error.Description, CorrelationID= str(qsBriefcase.CorrelationID), ScoreRequestID= qsBriefcase.ScoreRequestID)
        methodResponse = "{\"DNBUK_REUSEResponse\":\" Old DNB Data found : Error\" }"
        return methodResponse

    methodResponse = "{\"DNBUK_REUSEResponse\":\" Old DNB Data found :" + str(REUSEDUNANDBRADSTREET) + "\" }"

    #Skip the DNB call if data found for all locations that means NewClientInput collection size is 0
    if (REUSEDUNANDBRADSTREET):
        #add ReusedDNBData to backing store        
        jsonData = "{\"ReusedDNBData\":" + ObjectSerializer.serialize(oldDnBData) + "}"
        AddToBackingStore(backingStore, "", json.loads(jsonData))
        logging.info(jsonData)
    else:
        #add NewClientInput to backing store
        jsonData = "{\"NewClientInput\":" + ObjectSerializer.serialize(qsBriefcase.QSRequest.ClientInfoInput) + "}"
        AddToBackingStore(backingStore, "", json.loads(jsonData))
        logging.info(jsonData)
    if (qsBriefcase.NewClientInput == None):
        backingStore["dnbukskip"] = "1"
    #Skip DNB call if callDNB flag is no
    if (os.getenv("CallDNBServiceKey")=="No"): 
        backingStore["dnbukskip"] = "1"

    return methodResponse

def CustomMethod_DNBPostProcessing(parameters):
    inputPayload = parameters[0]
    backingStore = parameters[1]
    qsBriefcase = parameters[2]
    serviceToCall = parameters[3]
    logging.info("CustomMethod_DNBPostProcessing") 
    response = {}
    FinalDUNANDBRADSTREET = {}
    methodResponse = ""
    try:
        #save dnb data in OrchUKRCCQSOutputDnBService
        #create collection FinalDUNANDBRADSTREET
        if (qsBriefcase.NewClientInput != None):
            newDnBData = OrchUKRCCQSOutputDnBService()
            newDnBData.DunsNumber = GetValue(backingStore, "DUNANDBRADSTREETDUNSNUMBER".lower())
            newDnBData.ConfidenceCode = GetValue(backingStore, "DUNANDBRADSTREETCONFIDENCECODE".lower())
            newDnBData.CPCT = GetValue(backingStore, "DUNANDBRADSTREETCPCT".lower())
            newDnBData.AccountName = qsBriefcase.QSRequest.ClientInfoInput.ClientName
            newDnBData.StreetAddress1 = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationHouseNumberStreetName
            newDnBData.City = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationTown
            newDnBData.StreetAddress2 = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationLocalityName
            newDnBData.ZipCode = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationPostalCode
            newDnBData.Country = qsBriefcase.QSRequest.ClientInfoInput.ClientLocationCountry

            status = GetValue(backingStore, "DUNANDBRADSTREETStatusText")

            if (status.lower()!="success"):
                newDnBData.Error = status
            newDnBData.Sourcesystem = qsBriefcase.QSRequest.ScoreRequestInput.SourceSystem
            #newDnBData.DNBServiceResponse = json.dumps(qsBriefcase.AllResults["DNBUK"])
            #newDnBData.DNBServiceRequest = json.dumps(qsBriefcase.ServiceRequests["DNBUK"])
            newDnBData.SEUKConvBranchInputScoreRequestID = qsBriefcase.ScoreRequestInputID
            # Store the DnB Output data 
            SaveToDNBOutputService(newDnBData, qsBriefcase)
            FinalDUNANDBRADSTREET = newDnBData
        

        if (qsBriefcase.ReusedDNBData != None):
            FinalDUNANDBRADSTREET = qsBriefcase.ReusedDNBData
        #process test response
        if (qsBriefcase.ReusedDNBData == None and qsBriefcase.NewClientInput == None):
            DunsNumber = GetValue(backingStore, "DnBResponse.DUNSNumber")
            if (DunsNumber != None and DunsNumber!=""):
                testResponseDnBData = OrchUKRCCQSOutputDnBService()
                testResponseDnBData.DunsNumber = GetValue(backingStore, "DnBResponse.DUNSNumber")
                testResponseDnBData.ConfidenceCode = GetValue(backingStore, "DnBResponse.ConfidenceCodeValue")
                testResponseDnBData.CPCT = GetValue(backingStore, "CreditResponse.RawScore")
                testResponseDnBData.AccountName = GetValue(backingStore, "Request.AccountName")
                testResponseDnBData.StreetAddress1 = GetValue(backingStore, "Request.StreetAddress1")
                testResponseDnBData.StreetAddress2 = GetValue(backingStore, "Request.StreetAddress2")
                testResponseDnBData.City = GetValue(backingStore, "Request.City")
                testResponseDnBData.ZipCode = GetValue(backingStore, "Request.ZipCode")
                testResponseDnBData.Country = GetValue(backingStore, "Request.Country")
                testResponseDnBData.Sourcesystem = GetValue(backingStore, "Request.SourceSystem")

                FinalDUNANDBRADSTREET = testResponseDnBData

        #add FinalDUNANDBRADSTREET to backing store
        if((type(FinalDUNANDBRADSTREET) is dict) and len(FinalDUNANDBRADSTREET)==0):
            jsonData : str = "{\"FinalDUNANDBRADSTREET\":null}" 
        else:
            jsonData : str = "{\"FinalDUNANDBRADSTREET\":" + ObjectSerializer.serialize(FinalDUNANDBRADSTREET) + "}"        
            
        AddToBackingStore(backingStore, "", json.loads(jsonData))

        methodResponse = "{\"DNBUKPostProcessingResponse\":\"Data Saved\"}"
  
        if (((type(FinalDUNANDBRADSTREET) is dict) and len(FinalDUNANDBRADSTREET)==0 ) or FinalDUNANDBRADSTREET.DunsNumber == None or FinalDUNANDBRADSTREET.DunsNumber==""):
            module = "DNBUSPostProcessing"
            warning = CodeDesc(Code = "DNB Error",Description = "DNB Data Not Found")
            qsBriefcase.Warnings.append(warning)
            SaveToEventLog(qsBriefcase.ScoreRequestInputID, "DNBUKPostProcessing", Constants.Char_Status_Failed, warning.Code, module, warning.Description, CorrelationID = qsBriefcase.CorrelationID, ScoreRequestID =qsBriefcase.ScoreRequestID )
        return methodResponse
    
    except Exception as e:
        methodResponse = "{\"DNBUKPostProcessingResponse\":\"Data Save Error \"}"
        return methodResponse      
    
def CustomMethod_FE(parameters):
    """
    Custom Method for Features Engineering
    """
    from .ScoringOrchestratorFunction import call_post_service

    inputPayload = parameters[0]
    backingStore = parameters[1]
    briefcase = parameters[2]
    serviceToCall = parameters[3]
    request = briefcase.Request

    logging.info("CustomMethod_FE")                    

    response = {}
    methodResponse = ""
    ServiceStartTime = datetime.now()

    try:
        # Create FE payload
        jsonObject = {}

        # Call FE
        briefcase.Stage = "FE"
        briefcase.Status = "CallingService"
        inputPayload = json.dumps(jsonObject)
        briefcase.ServiceRequests[serviceToCall.ServiceContractName] = inputPayload
        serviceKey = get_env_var("FEURL")

        logging.info(serviceKey)
        logging.info(inputPayload)
        
        logging.info("FECall Started")
        logging.info(ServiceStartTime)

        response = call_FE(jsonObject)
        logging.info("FECall ended")

        # Process FE response
        briefcase.HttpStatusCode = 200
        briefcase.OverallEndTime = datetime.now()
        backingStore[
            serviceToCall.ServiceContractName.lower() + "httpstatus"
        ] = "200"
        outputPayload = json.dumps(response)        

        logging.info("Service Call finished for " + serviceToCall.ServiceContractName)
        if (response != None) & (briefcase.HttpStatusCode == 200):
            # 3. add result of service to breifcase
            briefcase.AllResults[serviceToCall.ServiceContractName] = response

            # 4. check custom status
            if "status" in response:
                customestatus = response["status"].title()
            elif "error_msg" in response:
                customestatus = response["error_code"]
            else:
                customestatus = "Failed"

            if customestatus != None:
                briefcase.CustomStatus = customestatus
                backingStore[
                    serviceToCall.ServiceContractName.lower() + "status"
                ] = customestatus      

        briefcase.AllResults["FeaturesEngineering"] = response
        return response                  
    
    except Exception as e:
        logging.info(e)
        methodResponse = '{"FECallResponse":"FE Call Error "}'
        save_to_response_service(
            briefcase,
            serviceToCall.ServiceContractName,
            inputPayload,
            methodResponse,
            ServiceStartTime,
            0,
        )
        return methodResponse    