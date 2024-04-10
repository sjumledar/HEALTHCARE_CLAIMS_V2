from queue import Empty
class ScoringOrchestratorServiceContractInput:
    def __init__(self):  
        self.ScoringOrchestratorServiceContractInputId = None
        self.ScoringOrchestratorId = None
        self.ServiceContractId = None
        self.AlgorithmId = None
        self.AlgorithmVersion = None
        self.ServiceContractInputParameterName = None
        self.ServiceContractInputParameterDataType = None
        self.ServiceContractInputParameterSource = None
        self.ServiceContractInputParameterDestination = None
        self.ServiceContractInputParameterDefaultValue = None
        self.ServiceContractInputParameterMandatoryRule = None
        self.ActiveStartDateTime = None
        self.ActiveEndDateTime = None