
class PredictorOutput:
    def __init__(self):
        self.PredictorName = ""
        self.PredictorValue = ""
        self.PredictorBinValue = ""
    
    def __init__(self,predictorValue,predictorBinValue,predictorName):        
        self.PredictorName = predictorName
        self.PredictorValue = predictorValue
        self.PredictorBinValue = predictorBinValue