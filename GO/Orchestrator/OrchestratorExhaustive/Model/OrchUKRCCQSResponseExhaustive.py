from .ScoringOutput import ScoringOutput
from json import JSONEncoder
import datetime
class OrchUKRCCQSResponseExhaustiveEncoder(JSONEncoder):
        def default(self, o):
            try:
                return o.__dict__     
            except Exception as e:
                if(isinstance(o, datetime.date)):                   
                    return o.strftime("%Y-%m-%d %H:%M:%S")
                else:
                   pass

class OrchUKRCCQSResponseExhaustive:
    def __init__(self):
        self.Errors = []
        self.Warnings = []

        self.CorrelationID = ""
        self.ScoreRequestInputID = None
        self.ScoreRequestID = ""
        self.SubmissionNumber = ""
        self.RequestStatus = ""
        self.Stage  = ""
        self.OverallStartTime = None
        self.OverallEndTime = None
        self.ScoringOutput : ScoringOutput = None
        self.ReasonOutputs  = []

        self.AllResults = {}
        self.Policy = None
  
    def __init__(self, bs):
        if bs:
            self.CorrelationID = str(bs.CorrelationID)
            self.ScoreRequestInputID = bs.ScoreRequestInputID
            self.ScoreRequestID = bs.ScoreRequestID
            self.SubmissionNumber = bs.SubmissionNumber
            self.RequestStatus = bs.Status
            self.Stage = bs.Stage
            self.OverallStartTime = bs.OverallStartTime
            self.OverallEndTime = bs.OverallEndTime
            self.ScoringOutput : ScoringOutput = ScoringOutput()
            self.ReasonOutputs = []
            self.AllResults = {}
            self.Policy = bs.QSRequest.PolicyInput            
            self.Errors = bs.Errors
            self.Warnings = bs.Warnings
    # @property
    # def Errors(self):
    #     if self.Errors is None:
    #         self.Errors = []
    #     return self.Errors

    # @Errors.setter
    # def Errors(self, value):
    #     self.Errors = value

    # @property
    # def Warnings(self):
    #     if self.Warnings is None:
    #         self.Warnings = []
    #     return self.Warnings

    # @Warnings.setter
    # def Warnings(self, value):
    #     self.Warnings = value

