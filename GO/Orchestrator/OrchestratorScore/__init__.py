import logging

import azure.functions as fx2
from ..OrchestratorExhaustive import *
from ..OrchestratorExhaustive.Model.OrchUKRCCQSResponse import *
from ..OrchestratorExhaustive.Model.OrchUKRCCQSResponseExhaustive import *

def main(req: fx2.HttpRequest) -> fx2.HttpResponse:
     logging.info("Orchestrator Score function processed a request.")
     try:
          req_bodyOrig = req.get_body().decode()
          req_body = json.loads(req_bodyOrig)
     except:
          OrchUKRCCQSInputScoreRequestID = SaveToInputRequestJson(req.get_body(), "Score")
          return fx.HttpResponse(
               "Invalid Json InputScoreRequestID :" + str(OrchUKRCCQSInputScoreRequestID),
               mimetype= "application/json",
               status_code=200
          )

     if req_body:
          hcResEx = ScoreCommon(req_body, req_bodyOrig, "Score")                       
          hcRes = trimExhuastiveResponse(hcResEx)
          return fx.HttpResponse(
               hcRes,
               mimetype= "application/json",
               status_code=200
          )
     else:
          return fx.HttpResponse(
               "This HTTP triggered function not executed successfully.",
               mimetype= "application/json",
               status_code=200
          )

def trimExhuastiveResponse(resExhaustive):
     hcRes : OrchUKRCCQSResponse = OrchUKRCCQSResponse()
     resExhaust = json.loads(resExhaustive)
     hcRes.ScoreRequestID = resExhaust["ScoreRequestID"]
     hcRes.SubmissionNumber = resExhaust["SubmissionNumber"]
     hcRes.RequestStatus = resExhaust["RequestStatus"]
     hcRes.Stage = resExhaust["Stage"]
     hcRes.Errors = resExhaust["Errors"]
     hcRes.SubmissionNumber = resExhaust["SubmissionNumber"]
     hcRes.Policy = resExhaust["Policy"]
     hcRes.CorrelationID = resExhaust["CorrelationID"]
     hcRes.ScoringOutput = resExhaust["ScoringOutput"]
     #hcRes.ReasonOutputs = resExhaust["ReasonOutputs"]

     #supress Code = Constants.DataConversionError warning
     for warning in resExhaust["Warnings"]:
          if ( warning["Code"] != Constants.DataConversionError):
               hcRes.Warnings.append(warning)
     return OrchUKRCCQSResponseEncoder().encode(hcRes)