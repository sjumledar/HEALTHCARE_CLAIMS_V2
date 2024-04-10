# Databricks notebook source
## a more recent version of sklearn is required for tweedie regression
%pip install scikit-learn==0.23.2

## install cloudpickle version
%pip install cloudpickle==1.6.0

# COMMAND ----------

# dbutils.widgets.removeAll()

## Notebook parameters
dbutils.widgets.text("1.SADEV Storage Folder", "")
uModelName = dbutils.widgets.get("1.SADEV Storage Folder")
# uModelName = ""

# COMMAND ----------

## load libraries
import pandas as pd
import numpy as np
import sklearn
from sklearn import linear_model
import cloudpickle
from sys import version_info

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Check Python version
# MAGIC -- must be compatible with cluster where pickle file will be used

# COMMAND ----------

PYTHON_VERSION = "{major}.{minor}.{micro}".format(major=version_info.major, minor=version_info.minor, micro=version_info.micro)
print(PYTHON_VERSION)

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Load training data

# COMMAND ----------

data_raw = pd.read_csv("/dbfs/mnt/sa-dev-files/" + uModelName + "/model_data.csv")
data_raw = pd.DataFrame([["a1", 1, 0, 1, 2, 1], ["b2", 1, 1, 1, 0, 3], ["c3", 0, 0, 1, 3, 1]]
                        , columns = ["CORRELATIONID", "PREDICTOR1", "PREDICTOR2", "PREDICTOR3", "TARGET", "WEIGHT"])

## data filters
## data transformations

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Select modeling data

# COMMAND ----------

data_model = data_raw[["PREDICTOR1", "PREDICTOR2", "PREDICTOR3", "TARGET", "WEIGHT"]]

## select target variable
target = data_model.loc[:,'TARGET'].values

## select weights variable
weights = data_model.loc[:,'WEIGHT'].values

## select predictors
train = data_model.drop(columns=["TARGET", "WEIGHT"])

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Fit model
# MAGIC -- estimates can be modified to replicate R results

# COMMAND ----------

model = linear_model.TweedieRegressor(power=1.7, alpha=0, link="log")
model.fit(train, target, weights)
print(model.coef_)
print(model.intercept_)

## modify coefficients
model.coef_ = [1, 2, 3]
model.intercept_ = .1
print(model.coef_)
print(model.intercept_)

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Save the model to blob

# COMMAND ----------

cloudpickle.dump(model, open("/dbfs/mnt/sa-dev-files/" + uModelName + "/model.pkl", 'wb'))

# COMMAND ----------

# MAGIC %md
# MAGIC 
# MAGIC # Predict on test data

# COMMAND ----------

test = data_model[["PREDICTOR1", "PREDICTOR2", "PREDICTOR3"]]
data_model["PREDICTIONS"] = model.predict(test)

display(data_model)

# COMMAND ----------


