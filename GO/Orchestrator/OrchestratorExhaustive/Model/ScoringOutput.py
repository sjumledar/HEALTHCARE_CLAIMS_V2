import json
class ScoringOutput:
    def __init__(self):        
        self.ScoreStatus = None
        self.OverallScore = None
        self.ELScore = None
        self.GLScore = None
        self.PropScore = None
    
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)        