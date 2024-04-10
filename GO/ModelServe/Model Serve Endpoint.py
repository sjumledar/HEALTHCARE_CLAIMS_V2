# Databricks notebook source
# MAGIC %md
# MAGIC # Pre modeling
# MAGIC 
# MAGIC 1. Use the SA_AZURE_ML_SMALL cluster. Make sure to create the pickle files using the same cluster as old python versions cannot unpickle new files <br>
# MAGIC 2. Fill Model Name. This name will appear in the Models UI. (Optional inputs 2 and 3 are for testing using script. Create API Key if testing using script, else use the Request/Response boxes in the Models UI)
# MAGIC 3. Edit Cmd8 based on the project ISD.
# MAGIC 4. Run Cmd1 - Cmd17

# COMMAND ----------

# MAGIC %md
# MAGIC ### Load environment

# COMMAND ----------

## a more recent version of sklearn is required for tweedie regression
%pip install scikit-learn==0.23.2

## install cloudpickle version
%pip install cloudpickle==1.6.0

# COMMAND ----------

# dbutils.widgets.removeAll()

## Notebook parameters
dbutils.widgets.text("1.Model Name", "")
uModelName = dbutils.widgets.get("1.Model Name")
uModelName = "TEST_DEV"

dbutils.widgets.text("2.Model URL", "")
uModelURL = dbutils.widgets.get("2.Model URL")
uModelURL = "https://adb-1606981283391157.17.azuredatabricks.net/model/"

dbutils.widgets.text("3.API Key", "")
uAPIKey = dbutils.widgets.get("3.API Key")
uAPIKey = "dapi9a865dc6b688a9906ce22844c559f67c"

# COMMAND ----------

import pandas as pd
import numpy as np
import time
import mlflow
import mlflow.sklearn
import pickle
import cloudpickle
import json
import pyspark
import sklearn
import cerberus
from sklearn import linear_model
from sys import version_info

# COMMAND ----------

## create a conda environment for the MLflow model containing all necessary dependencies. Upon registering the model, the dependencies should reflect from the logs for monitoring if a library was not installed
PYTHON_VERSION = "{major}.{minor}.{micro}".format(major=version_info.major,
                                                  minor=version_info.minor,
                                                  micro=version_info.micro)
MLFLOW_VERSION = mlflow.__version__
SKLEARN_VERSION = sklearn.__version__
CLOUDPICKLE_VERSION = cloudpickle.__version__

conda_env = {
    'channels': ['conda-forge','defaults'],
    'dependencies': [
      'python={}'.format(PYTHON_VERSION),
      'scikit-learn=={}'.format(SKLEARN_VERSION),
      'cloudpickle=={}'.format(CLOUDPICKLE_VERSION),
      'pip',
      'pyspark',
      'cerberus',
      {
        'pip': [
          'mlflow',
          'azureml-defaults'
        ],
      },
    ],
    'name': 'mlflow-env'
}

# COMMAND ----------

# MAGIC %md
# MAGIC ### Create a custom predict function. This serves as the scoring function of the registered model in MLflow.

# COMMAND ----------

## custom class that wraps sklearn model and predict
class CustomResponseModel(mlflow.pyfunc.PythonModel):
  pd = __import__('pandas')
  np = __import__('numpy')
  time = __import__('time')
  json = __import__('json')
  cerberus = __import__('cerberus')
  
  def __init__(self, model):
    self.sklearn_model = model

  def predict(self, context, model_input):
    
    ## convert non predictor_list fields to df
    other_input_0 = model_input[["CORRELATIONID"]].head(1)
    
    ## extract predictors from the predictor_list field and convert to df
    predictor_df = pd.json_normalize(model_input.iloc[0]['VARIABLE_LIST'])
    predictor_df2 = predictor_df.set_index("VARIABLE_NAME").transpose().reset_index(drop=True)
    predictor_df2.columns.name = ''
    model_input_0 = predictor_df2.head(1)
    
    ## join both df
    data = pd.concat([other_input_0, model_input_0], axis=1)
    
    ## VALIDATE USING CERBERUS. CAN BE DONE ON EITHER model_input_0 or data

    ## transform dataframe to dict
    data_dict = data.to_dict(orient='records')
    body = json.loads(json.dumps(data_dict)[1:-1])
    
    ## define expected schema of payload. HOW ABOUT 300-COLUMN INPUT? TO TEST ALL SCENARIO?
    schema = {"CORRELATIONID": {"type": "string", "required": True, "empty": False},
              "datetime": {"type": "string", "required": True, "empty": False},
              "url": {"type": "string", "required": True, "empty": False},
              "method": {"type": "string", "required": True, "empty": False},
              "error_msg": {"type": "string", "required": True, "empty": False},
              "user": {"type": "string", "required": True, "empty": False}
             }
    output = {}
    status = 'success'
    status_code = 200
    validator = cerberus.Validator()
    result = validator.validate(body, schema)

    if result:
      ## insert transformation, scoring, output processing here
      temp_output = {}
      temp_output["CORRELATIONID"] = data['CORRELATIONID'][0]
      temp_output["SCORESTATUS"] = "Completed"
      temp_output["SCORE"] = "3"
      temp_output["REASONOUTPUT"] = [{"REASONGROUPNAME": data.columns[1] + "_RM", "REASONMESSAGETXT": "Average", "MESSAGECOLOR": "White", "PREDICTOROUTPUT": [{"PREDICTORNAME": data.columns[1], "PREDICTORVALUE": data[data.columns[1]][0], "PREDICTORBINVALUE": data[data.columns[1]][0]}]},{"REASONGROUPNAME": data['url'][0] + "_RM", "REASONMESSAGETXT": "Average", "MESSAGECOLOR": "White", "PREDICTOROUTPUT": [{"PREDICTORNAME": data.columns[2], "PREDICTORVALUE": data[data.columns[2]][0], "PREDICTORBINVALUE": data[data.columns[2]][0]}]}]
      output["OUTPUT"] = temp_output
      output["STATUS"] = status
      output["STATUS_CODE"] = status_code
      output["CORRELATIONID"] = "abc123"
      output["ERROR_MSG"] = validator.errors
    
    else:
      output["STATUS"] = "Bad Request"
      output["STATUS_CODE"] = 400
      output["ERROR_MSG"] = validator.errors
        
    ## output as json
#     return json.loads(temp_output)
#     return json.loads(json.dumps(output))
    return output
#     return data
#     return model_input

# COMMAND ----------

# MAGIC %md
# MAGIC # Train and log model in mlflow

# COMMAND ----------

with mlflow.start_run() as run:
  
  run_id = run.info.run_uuid

  print("MLflow:")
  print("  run_id:",run_id)
  print("  experiment_id:",run.info.experiment_id)
  
  ## for purpose of shell script, create a placeholder for the sklearn model. Import the actual pickle file inside the CustomResponseModel
#   model = linear_model.TweedieRegressor(power=1.5, alpha=0, link="log")
  model = 1

  ## Log model. note that this logged model has customized prediction and needs to me loaded using mlflow
  mlflow.pyfunc.log_model("model", python_model=CustomResponseModel(model), conda_env=conda_env)
  

# COMMAND ----------

# MAGIC %md
# MAGIC # Test the logged model

# COMMAND ----------

## import/create sample data for testing
test_data = pd.DataFrame([["abc123", [{"VARIABLE_NAME": "datetime", "VARIABLE_VALUE": "2022-01-25 22:17:49.424034"}, {"VARIABLE_NAME": "url", "VARIABLE_VALUE": "http:/test.azurewebsites.net/api/AZF_TEMPLATE"}, {"VARIABLE_NAME": "method", "VARIABLE_VALUE": "POST"}, {"VARIABLE_NAME": "error_msg", "VARIABLE_VALUE": "{}"}, {"VARIABLE_NAME": "user", "VARIABLE_VALUE": "SA_DATABRICKS_USER_1"}]]], columns = ["CORRELATIONID", "VARIABLE_LIST"])

test_data

# COMMAND ----------

# MAGIC %md
# MAGIC ### Using logged model with custom predict function

# COMMAND ----------

## load the logged model
run_info = run.info.run_uuid
model_uri = f'runs:/{run_info}/model'
model_flow = mlflow.pyfunc.load_model(model_uri)
model_flow

# COMMAND ----------

## predict on a dataframe
predictions = model_flow.predict(test_data)
predictions

# COMMAND ----------

# MAGIC %md
# MAGIC # MLflow registration and monitoring
# MAGIC 
# MAGIC 1. After registration, go to the mlflow models UI and enable serving. May take ~5 minutes

# COMMAND ----------

## register the model for serving
result = mlflow.register_model(
  model_uri,
  name = uModelName
)
version = result.version

# COMMAND ----------

## manage registered models using client, i.e., operations such as model stage transitions, delete a model or specific versions of a model
client = mlflow.tracking.MlflowClient()

## transition version
client.transition_model_version_stage(
    name = uModelName,
    version = version,
    stage = "Staging")

# COMMAND ----------

# ## transition a specific version
# client.transition_model_version_stage(
#     name = uModelName,
#     version = 12,
#     stage = "None")

# ## delete model version
# client.delete_model_version(
#   name = uModelName,
#   version = 15)

# ## delete a registered model along with all its versions
# client.delete_registered_model(
#   name="TEST_")


# COMMAND ----------

# MAGIC %md
# MAGIC # Test the served model
# MAGIC ---
# MAGIC Wait some time (5-10 minutes?) before the served model is Ready. Check the served model using the logs to see errors during registration as Pending status is unable to score

# COMMAND ----------

test_data = pd.DataFrame([["abc123", [{"VARIABLE_NAME": "datetime", "VARIABLE_VALUE": "2022-01-25 22:17:49.424034"}, {"VARIABLE_NAME": "url", "VARIABLE_VALUE": "http:/test.azurewebsites.net/api/AZF_TEMPLATE"}, {"VARIABLE_NAME": "method", "VARIABLE_VALUE": "POST"}, {"VARIABLE_NAME": "error_msg", "VARIABLE_VALUE": "{}"}, {"VARIABLE_NAME": "user", "VARIABLE_VALUE": "SA_DATABRICKS_USER_1"}]]], columns = ["CORRELATIONID", "VARIABLE_LIST"])
test_data

# COMMAND ----------

# MAGIC %md
# MAGIC ### Using the served model UI Request/Response boxes

# COMMAND ----------

## convert the dataframe to json and the use the json string in the API user interface to see the result.
d = test_data.to_dict(orient='records')
j = json.dumps(d)
print(j)

# COMMAND ----------

# MAGIC %md
# MAGIC ### Using python code to score a json object

# COMMAND ----------

## url, api_key, sample input are required here
import urllib.request
import json
import os
import ssl
import datetime

def allowSelfSignedHttps(allowed):
    if allowed and not os.environ.get('PYTHONHTTPSVERIFY', '') and getattr(ssl, '_create_unverified_context', None):
        ssl._create_default_https_context = ssl._create_unverified_context

allowSelfSignedHttps(True) # this line is needed if you use self-signed certificate in your scoring service.

#Databricks Serving
url = uModelURL + uModelName + '/Staging/invocations'
api_key = uAPIKey #'dapi9a865dc6b688a9906ce22844c559f67c'
headers = {'Content-Type':'application/json', 'Authorization':('Bearer '+ api_key)}

data = test_data.to_dict(orient='records')
body = str.encode(json.dumps(data))
req = urllib.request.Request(url, body, headers)

try:
    for x in range(0,1):
        start = time.time()
        response = urllib.request.urlopen(req)
        end = time.time()
        delta = end - start
        elapsed_seconds = round(delta, 2)
        result = response.read()
        print(elapsed_seconds)
        print(result)

except urllib.error.HTTPError as error:
    print("The request failed with status code: " + str(error.code))

    # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
    print(error.info())
    print(json.loads(error.read().decode("utf8", 'ignore')))

# COMMAND ----------


