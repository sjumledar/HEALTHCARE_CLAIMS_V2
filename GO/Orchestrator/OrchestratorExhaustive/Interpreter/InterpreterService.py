import json
import logging
import os


from ..Model.OrchUKRCCQSRequest import OrchUKRCCQSRequest
from ..Model import *
from ..Data.Dao import *
from ..Model.CodeDesc import CodeDesc
from ..Model.CodeDescModule import CodeDescModule

def RequestInterpreterService(req_body : str, req_bodyOrig : str, CorrelationID : str, context):

	#save Json in OrchUKRCCQSInputScoreRequest here and generate OrchUKRCCQSInputScoreRequestID
	OrchUKRCCQSInputScoreRequestID = SaveToInputRequestJson(req_bodyOrig,context)
	
	req_body = {k.lower():v for k,v in req_body.items()}
	scorerequestinput = {k.lower():v for k,v in req_body["scorerequestinput"].items()}
	transactiontype = scorerequestinput["transactiontype"].lower()
	
	#create request object
	reqObject = OrchUKRCCQSRequest.OrchUKRCCQSRequest()
	reqObject.ScoreRequestInputID = OrchUKRCCQSInputScoreRequestID 
	
	#populate reqObject
	reqObject.ScoreRequestInput = InputScoreRequest.InputScoreRequest()
	if "scorerequestinput" in req_body:
		parentField = req_body["scorerequestinput"]
		reqObject.ScoreRequestInput.ScoreRequestID = GetValue("str", parentField, "true", "ScoreRequestId", reqObject,minLength=7, maxLength=15)
		reqObject.ScoreRequestInput.TransactionType = GetValue("str", parentField, "true", "TransactionType", reqObject, allowed= ['New', 'Renewal'])
		reqObject.ScoreRequestInput.TransactionTimeStamp = GetDate("TransactionTimeStamp" ,GetValue("str", parentField,  "true", "TransactionTimeStamp", reqObject), reqObject,mandatory = "true")
		reqObject.ScoreRequestInput.SourceSystem = GetValue("str", parentField, "true", "SourceSystem", reqObject, allowed= ['UKRQuickScore', 'UKRQuickScore_Test', 'UKRQuickScore_SSTest','UKRQuickScore_BulkTest'])
		reqObject.ScoreRequestInput.SourceSystemAction = GetValue("str", parentField, "true", "SourceSystemAction", reqObject, allowed= ['Score'])
		reqObject.ScoreRequestInput.IsBulk = GetValue("str", parentField, "false", "IsBulk", reqObject)
		reqObject.ScoreRequestInput.ProductType = GetValue("str", parentField, "true", "ProductType", reqObject, allowed= ['Commercial Combined'])
		
	reqObject.PolicyInput = InputPolicy.InputPolicy()
	if "policyinput" in req_body:
		parentField = req_body["policyinput"]
		reqObject.PolicyInput.PolicyNumber = GetValue("str", parentField,  "false", "PolicyNumber", reqObject)
		reqObject.PolicyInput.EffectiveDate = GetDate("EffectiveDate" ,GetValue("str", parentField,  "true", "EffectiveDate", reqObject), reqObject,mandatory = "true")
		reqObject.PolicyInput.ExpirationDate = GetDate("ExpirationDate" ,GetValue("str", parentField,  "true", "ExpirationDate", reqObject), reqObject,mandatory = "true")
	
	reqObject.SubmissionInput = InputSubmission.InputSubmission()
	if "submissioninput" in req_body:
		parentField = req_body["submissioninput"]
		reqObject.SubmissionInput.SubmissionNumber = GetValue("str", parentField,  "true", "SubmissionNumber", reqObject)
		if (reqObject.SubmissionInput.SubmissionNumber != None):
			if(not reqObject.SubmissionInput.SubmissionNumber.upper().startswith("S")):
				reqObject.SubmissionInput.SubmissionNumber = "S" + reqObject.SubmissionInput.SubmissionNumber
		reqObject.SubmissionInput.SubmissionCreateDate = GetDate("SubmissionCreateDate" ,GetValue("str", parentField,  "true", "SubmissionCreateDate", reqObject), reqObject,mandatory = "true")
		reqObject.SubmissionInput.NatureOfBusiness = GetValue("str", parentField,  "false", "NatureOfBusiness", reqObject)
		reqObject.SubmissionInput.PropertyTotalExposureBanded = GetValue("str", parentField,  "true", "PropertyTotalExposureBanded", reqObject)
		reqObject.SubmissionInput.PropertyClaimsHistory5YrsBinary = GetValue("str", parentField,  "true", "PropertyClaimsHistory5YrsBinary", reqObject)

	reqObject.ClientInfoInput = InputClientInfo.InputClientInfo()
	if "clientinfoinput" in req_body:
		parentField = req_body["clientinfoinput"]
		reqObject.ClientInfoInput.ClientNumber = GetValue("int", parentField,  "true", "ClientNumber", reqObject)
		reqObject.ClientInfoInput.ClientName = GetValue("str", parentField,  "raiseWarning", "ClientName", reqObject)
		reqObject.ClientInfoInput.ClientLocationHouseNumberStreetName = GetValue("str", parentField, "raiseWarning", "ClientLocationHouseNumberStreetName", reqObject)
		reqObject.ClientInfoInput.ClientLocationLocalityName = GetValue("str", parentField, "false", "ClientLocationLocalityName", reqObject)
		reqObject.ClientInfoInput.ClientLocationTown = GetValue("str", parentField, "raiseWarning", "ClientLocationTown", reqObject)
		reqObject.ClientInfoInput.ClientLocationPostalCode = GetValue("str", parentField, "raiseWarning", "ClientLocationPostalCode", reqObject)
		reqObject.ClientInfoInput.ClientLocationCountry = GetValue("str", parentField, "raiseWarning", "ClientLocationCountry", reqObject)
		
	
	reqObject.TestResponsesInput = []
	if "testresponsesinput" in req_body:
		for testResponsesInput in req_body["testresponsesinput"]:
			reqObject.TestResponsesInput.append(testResponsesInput)

	
	#reqObject.Errors = errors
	reqObject.CorrelationID = CorrelationID

	#save inputs here
	SaveToInput(reqObject)
	return reqObject



def GetValue(datatype, parentField, mandatory, objectFieldName, reqObject, id = -1, idfieldname="", allowed=None, minLength=None, maxLength=None):
	try:
		objectFieldValue = None
		parentField = {k.lower():v for k,v in parentField.items()}
		if objectFieldName.lower() in parentField:    
			objectFieldValue = 	parentField[objectFieldName.lower()]		
			if(objectFieldValue=="" and mandatory=="true"):
				AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname)
				return None
			elif(objectFieldValue==""):
				AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname)
				return None
			else:
					if datatype == "str":
						if(allowed!=None):
							allowed = [x.lower() for x in allowed]
							#check if the values are allowed
							if((str(objectFieldValue)).lower() in allowed):
								return str(objectFieldValue)
							else:
								AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname, allowed)
								return None
						#check min and max lenght
						elif(minLength!=None and len(objectFieldValue) <minLength):
							AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname, minLength=minLength)
							return str(objectFieldValue)
						elif(maxLength!=None and len(objectFieldValue) >maxLength):		
							AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname, maxLength=maxLength)
							return str(objectFieldValue)
						else:
							return str(objectFieldValue)
					elif datatype == "int":
						return int(objectFieldValue)
					elif datatype == "number":
						return float(objectFieldValue)
					else:
						return str(objectFieldValue)
		else:
			AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname)
			return None

	except Exception as e:
		AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id, idfieldname)
		return None


def GetDate(DateFieldName ,DateFieldValue, reqObject,mandatory,id = -1, idfieldname=""):
	try:
		if(DateFieldValue ==None or DateFieldValue =="" or DateFieldValue =='None'):
			return None
		else:
			return (datetime.strptime(DateFieldValue, '%Y-%m-%d %H:%M:%S.%f'))
	except:
		pass
	try:
		return (datetime.strptime(DateFieldValue, '%Y-%m-%d %H:%M:%S'))
	except:
		pass
	try:
		return (datetime.strptime(DateFieldValue, '%Y-%m-%d'))
	except:
		AddErrorOrWarningMessage(DateFieldValue, mandatory, DateFieldName, reqObject, id, idfieldname)


def AddErrorOrWarningMessage(objectFieldValue, mandatory, objectFieldName, reqObject, id = -1, idfieldname="", allowed=None, minLength=None, maxLength=None):
	addId = ""
	addAllowedvalues =""
	addMinLength =""
	addMaxLength =""
	if (id != -1 and id!=None):
		addId = " for " +idfieldname+":" + str(id)
	if(allowed!=None):
		if(len(allowed)==1):
			addAllowedvalues = ", Valid value is " + (','.join(allowed))
		else:
			addAllowedvalues = ", Valid values are " + (','.join(allowed))
	if(minLength!=None):
		addMinLength = ", Value should be minimum "+ str(minLength) +" characters"
	if(maxLength!=None):
		addMaxLength = ", Value should be maximum "+ str(maxLength) +" characters"	
	if (mandatory =="true"):
		reqObject.Errors.append(CodeDescModule (Code = "SchemaValidationError", Description = objectFieldName + " Not Valid" + addId + addAllowedvalues + addMinLength + addMaxLength, Module = "OrchUKRCCQSInterpreterService"))
	elif (mandatory =="raiseWarning"):
		reqObject.Warnings.append(CodeDesc (Code = "SchemaValidationWarning", Description = objectFieldName + " Not Supplied" + addId + addAllowedvalues + addMinLength + addMaxLength))

	# elif (CoreValidationUtils.IsValueNotEmpty(value) && CoreValidationUtils.HasSpecialChar(objectFieldValue, myFieldInfo.FieldType.FullName, excludeSpecialCharcheck)):
	# 	if (mandatory=="true")
	# 		request.Errors.append(CodeDescModule (Code = "SchemaValidationError", Description = objectFieldName + " contains invalid characters " + addId, Module = "Module_HcMiscFacInterpreterService")
	# 	else
	# 		request.Warnings.append(CodeDesc (Code = "SchemaValidationWarning", Description = objectFieldName + " contains invalid characters "))



def case_insensitive_key(a,k):
    k = k.lower()
    return [a[key] for key in a if key.lower() == k]