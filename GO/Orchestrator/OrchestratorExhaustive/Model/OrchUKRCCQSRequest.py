
class OrchUKRCCQSRequest:
    def __init__(self):
        self._errors = None
        self._schemaValidationErrors = None
        self._warnings = None
        self.ScoreRequestInput = None
        self.PolicyInput = None
        self.SubmissionInput = None        
        self.ClientInfoInput = None
        self.TestResponsesInput = []
        self.ScoreRequestInputID = None
        self.CorrelationID = None

    @property
    def Errors(self):
        if self._errors is None:
            self._errors = []
        return self._errors

    @Errors.setter
    def Errors(self, value):
        self._errors = value

    @property
    def SchemaValidationErrors(self):
        if self._schemaValidationErrors is None:
            self._schemaValidationErrors = []
        return self._schemaValidationErrors

    @SchemaValidationErrors.setter
    def SchemaValidationErrors(self, value):
        self._schemaValidationErrors = value

    @property
    def Warnings(self):
        if self._warnings is None:
            self._warnings = []
        return self._warnings

    @Warnings.setter
    def Warnings(self, value):
        self._warnings = value
