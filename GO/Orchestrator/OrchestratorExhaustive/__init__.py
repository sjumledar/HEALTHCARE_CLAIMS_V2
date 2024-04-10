import logging
import azure.functions as fx
import json
import logging
import uuid
import cerberus as cbrs
from .Model.OrchUKRCCQSResponseExhaustive import OrchUKRCCQSResponseExhaustiveEncoder
from .Model.OrchUKRCCQSBriefcase import OrchUKRCCQSBriefcase
from .Model.OrchUKRCCQSRequest import OrchUKRCCQSRequest
from .Model.Metadata import *
from .Data import *
from .Interpreter.InterpreterService import *
from .Model.OrchUKRCCQSBriefcase import OrchUKRCCQSBriefcase
from .Model.OrchUKRCCQSRequest import OrchUKRCCQSRequest
from .Model.Metadata import *
from .Orchestrator.ScoringOrchestratorFunction import *

def main(req: fx.HttpRequest) -> fx.HttpResponse:
    logging.info("Orchestrator Exhaustive function processed a request.")    
    try:
        req_bodyOrig = req.get_body().decode()
        req_body = json.loads(req_bodyOrig)
    except:
        OrchUKRCCQSInputScoreRequestID = SaveToInputRequestJson(req.get_body(), "ScoreExhaustive")
        return fx.HttpResponse(
            "Invalid Json InputScoreRequestID :" + str(OrchUKRCCQSInputScoreRequestID),
            mimetype= "application/json",
            status_code=200
        )
    if req_body:
        commonresponse = ScoreCommon(req_body, req_bodyOrig, "ScoreExhaustive")                       
        return fx.HttpResponse(
            commonresponse,
            mimetype= "application/json",
            status_code=200
        )
    else:
        return fx.HttpResponse(
            "This HTTP triggered function not executed successfully.",
            mimetype= "application/json",
            status_code=200
        )

def ScoreCommon(req_body, req_bodyOrig, context):
    #1.get payload
    stage : str = "ScoreCommon Started"

    #2.validate payload and create Request Object
    correlationID : str = str(uuid.uuid4())
    qsRequest : OrchUKRCCQSRequest() = RequestInterpreterService(req_body, req_bodyOrig, correlationID, context)
    stage = "ValidationCompleted"

    #3.Create Briefcase,response
    qsBriefcase = OrchUKRCCQSBriefcase.OrchUKRCCQSBriefcase()    

    #4.Populate Briefcase with initial values
    qsBriefcase.OverallStartTime = datetime.now()
    qsBriefcase.CorrelationID = correlationID
    qsBriefcase.QSRequest = qsRequest
    qsBriefcase.Context = context
    qsBriefcase.ScoreRequestID = qsRequest.ScoreRequestInput.ScoreRequestID
    qsBriefcase.SubmissionNumber = qsRequest.SubmissionInput.SubmissionNumber
    qsBriefcase.ScoreRequestInputID = qsRequest.ScoreRequestInputID
    qsBriefcase.AllResults["qsRequest"] = qsRequest
    if (len(qsRequest.Warnings) > 0):
        qsBriefcase.Warnings=qsRequest.Warnings
    if (len(qsRequest.Errors) > 0) or (len(qsRequest.SchemaValidationErrors) > 0):
        qsBriefcase.Stage = stage
        qsBriefcase.Errors=qsRequest.SchemaValidationErrors
        qsBriefcase.Errors.extend(qsRequest.Errors)
    else:
        qsBriefcase.Stage = "BriefcaseInitialized"
        #5.Fetch Metadata for Orchestrator
        orchestratorIdentifier : OrchestratorIdentifier = OrchestratorIdentifier()
        orchestratorIdentifier.ScoringOrchestratorId = 6
        orchestratorIdentifier.ScoreIdentifier = qsBriefcase.ScoreRequestID
        orchestratorIdentifier.ArchBusiness = "UKR CC QuickScore"
        orchestratorIdentifier.LineOfBusiness = "UKRegional"
        orchestratorIdentifier.Coverage = "QS"
        orchestratorSummary : OrchestratorSummary = Repository.FetchModelData(orchestratorIdentifier)
        #6.Call Services based on Sequencer
        qsBriefcase = RunActivity(qsBriefcase,orchestratorSummary,req_body,correlationID)
        
    response = CreateExhaustiveResponse(qsBriefcase)
    SaveToResponseScore(qsBriefcase)
    SaveToOutputScore(qsBriefcase, response, "")
    return response  

def CreateExhaustiveResponse(qsBriefcase):
    qsResEx = OrchUKRCCQSResponseExhaustive.OrchUKRCCQSResponseExhaustive(qsBriefcase)
    so : ScoringOutput = ScoringOutput.ScoringOutput()
    if(qsBriefcase.OverallScore):
        so.OverallScore = qsBriefcase.OverallScore
    if(qsBriefcase.ELScore):
        so.ELScore = qsBriefcase.ELScore    
    if(qsBriefcase.GLScore):
        so.GLScore = qsBriefcase.GLScore    
    if(qsBriefcase.PropScore):
        so.PropScore = qsBriefcase.PropScore    
    if (len(qsBriefcase.Errors) > 0):
        so.ScoreStatus = "Completed with Errors"
    elif (len(qsBriefcase.Warnings) > 0):
        so.ScoreStatus = "Completed with Warnings"
    else:
        so.ScoreStatus = "Completed"

    qsResEx.ScoringOutput = so

    qsResEx.Policy = qsBriefcase.QSRequest.PolicyInput

    qsResEx.Warnings = qsBriefcase.Warnings
    qsResEx.Errors = qsBriefcase.Errors
    qsResEx.AllResults = {}
    for allresultKey, allresultValue in qsBriefcase.AllResults.items():
        if (allresultKey !="qsRequest"):
            qsResEx.AllResults[allresultKey] = allresultValue     
    if len(qsResEx.AllResults) == 0:
        qsResEx.AllResults = None
    if qsBriefcase.ReasonOutputs!=None and len(qsBriefcase.ReasonOutputs) == 0:
        qsResEx.ReasonOutputs = None
    else:
        qsResEx.ReasonOutputs = qsBriefcase.ReasonOutputs
    qsResEx.Stage = qsBriefcase.Stage
    qsResEx.RequestStatus = "Completed"
    qsResEx.OverallStartTime = str(qsBriefcase.OverallStartTime)
    if(qsBriefcase.OverallEndTime):
        qsResEx.OverallEndTime = str(qsBriefcase.OverallEndTime)

    returnstr :str = OrchUKRCCQSResponseExhaustiveEncoder().encode(qsResEx)
    

    return returnstr