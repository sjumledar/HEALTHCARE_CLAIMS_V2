from queue import Empty
class ScoringOrchestratorSequencer:
    def __init__(self):         
        self.ScoringOrchestratorSequencerId = None
        self.ScoringOrchestratorId = None
        self.SequencerName = None
        self.SequencerCategory = None
        self.SequencerOrder = None
        self.ChildServiceContract = None
        self.ActiveStartDateTime = None
        self.ActiveEndDateTime = None