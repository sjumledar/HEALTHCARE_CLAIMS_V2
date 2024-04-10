from queue import Empty
class OrchestratorIdentifier:
    def __init__(self): 
        self.ScoringOrchestratorId = None
        self.ScoreIdentifier = None
        self.ArchBusiness = None
        self.LineOfBusiness = None
        self.Coverage = None
        self.TransType = None
    
    def sort(self):
        print("sorted")