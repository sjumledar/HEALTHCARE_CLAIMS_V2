from queue import Empty
import json

class OrchUKRCCQSBriefcase:
    def __init__(self):
        self.Errors = []
        self.Warnings = []
        self.AllResults = {}
        self.CorrelationID = None
        self.ScoreRequestInputID = None
        self.ScoreRequestID = None
        self.SubmissionNumber = None
        self.Context = None
        self.Stage = None
        self.Status = None
        self.ScoreStatus = None
        self.OverallScore = None
        self.ELScore = None
        self.GLScore = None
        self.PropScore = None
        self.HttpStatusCode = None
        self.CustomStatus = None
        self.ResponseServiceID = None
        self.OverallStartTime = None
        self.OverallEndTime = None
        self.QSRequest = None
        self.ReasonOutputs = None
        self.ServiceRequests = {}
        self.ReusedDNBData = None
        self.NewClientInput = None
        self.VariableInputNLP = None

class VariableInput:
    def __init__(self,variableName,variableValue):
       self.VariableName  = variableName
       self.VariableValue = variableValue
    
    def to_json(self):
        return json.dumps(self)