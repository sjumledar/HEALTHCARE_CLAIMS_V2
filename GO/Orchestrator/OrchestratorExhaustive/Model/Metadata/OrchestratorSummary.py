from queue import Empty


class OrchestratorSummary:
    def __init__(self): 
        self.ScoringOrchestratorId = None
        self.ScoreIdentifier = None
        self.ArchBusiness = None
        self.LineOfBusiness = None
        self.Coverage = None
        self.ScoringOrchestratorId = None
        self.ScoreIdentifier = None
        self.TransType = None
        self.LineOfBusiness = None
        self.AlgorithmId = None
        self.AlgorithmVersion = None
        self.ServiceContracts  = [] #List<ServiceContract>
        self.Sequencers = [] #List<ScoringOrchestratorSequencer>
        self.AlgorithmStartDate = None
        self.AlgorithmEndDate = None
  
        