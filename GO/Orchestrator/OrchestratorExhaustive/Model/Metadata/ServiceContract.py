from queue import Empty
class ServiceContract:
    def __init__(self):  
        self.ServiceContractId = None
        self.ServiceContractName = None
        self.ServiceContractDescription = None
        self.ServiceContractCategory = None
        self.ServiceContractInputs = None
        self.ServiceContractOutputs = None
        self.ActiveStartDateTime = None
        self.ActiveEndDateTime = None
        self.ServiceKey = None
        self.ServiceKeyType = None
        self.SecurityTokenKey = None
        self.IsDurableFunction = None
        self.DurableFunctionStatusURLField = None
        self.DurableFunctionStatusField = None
        self.DurableFunctionResultURLField = None
        self.DurableFunctionTimeoutInSeconds = None
        self.DurableFunctionRetryCount = None