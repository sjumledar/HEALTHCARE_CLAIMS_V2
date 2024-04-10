import json
from json import JSONEncoder
import datetime
class ObjectSerializer(object):
    @staticmethod
    def serialize(obj):
        def check(o):
            for k, v in o.__dict__.items():
                try:
                    _ = json.dumps(v)
                    o.__dict__[k] = v
                except TypeError:
                    o.__dict__[k] = str(v)
            return o
        return json.dumps(check(obj).__dict__, indent=2)    

     