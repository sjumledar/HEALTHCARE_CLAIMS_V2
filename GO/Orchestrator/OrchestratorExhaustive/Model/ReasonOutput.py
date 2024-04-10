import json
class ReasonOutput:
    def __init__(self):
        self.ReasonGroupName = ""
        self.ReasonMessageTxt = ""
        self.MessageColor = ""
        self.PredictorOutputs = []

    def __init__(self,messageColor,reasonMessageTxt,reasonGroupName):
        self.ReasonGroupName = reasonGroupName
        self.ReasonMessageTxt = reasonMessageTxt
        self.MessageColor = messageColor

    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)                

