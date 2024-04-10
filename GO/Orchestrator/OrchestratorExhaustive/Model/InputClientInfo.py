import json

class InputClientInfo:
    def __init__(self):
        self.ClientNumber = None 
        self.ClientName = None 
        self.ClientLocationHouseNumberStreetName = None 
        self.ClientLocationLocalityName = None 
        self.ClientLocationTown = None 
        self.ClientLocationPostalCode = None 
        self.ClientLocationCountry = None 
    def toJson(self):
        return json.dumps(self, default=lambda o: o.__dict__)