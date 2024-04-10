from .ScoringOutput import ScoringOutput
from json import JSONEncoder
class OrchUKRCCQSResponseEncoder(JSONEncoder):
        def default(self, o):
            return o.__dict__     

class OrchUKRCCQSResponse:
    def __init__(self):
        self.ScoreRequestID = ""
        self.SubmissionNumber = ""
        self.CorrelationID = ""
        self.RequestStatus = ""
        self.Stage  = ""
        self.ScoringOutput : ScoringOutput = None
        #self.ReasonOutputs  = []
        self.Warnings = []
        self.Errors = [] 
        self.Policy = None 
    

