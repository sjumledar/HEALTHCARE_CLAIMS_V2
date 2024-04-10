import logging
import os
import urllib

import cerberus as c
import pandas as pd
import pyodbc
from snowflake.sqlalchemy import URL
from sqlalchemy import *
from sqlalchemy import create_engine, engine
from sqlalchemy.pool import QueuePool


# Define expected schema of payload
schema = {
    "Submission": {
        "type": "dict",
        "schema": {
            "CorrelationID": {"type": "string", "required": False, "empty": False},
            "SubmissionNumber": {"type": "integer", "required": False, "empty": False},
        }
    }
}


# Input validation
def validate_input(input, schema=schema):
    output = {}
    status = 'Success'
    status_code = 200
    if not input:
        output["STATUS"] = "Bad Requst"
        output["STATUS_CODE"] = 400
        output["ERRORS"] = "Please pass a valid json payload in the request body"
    else:
        validator = c.Validator()
        result = validator.validate(input, schema)
        
        if result:
            output["STATUS"] = status
            output["STATUS_CODE"] = status_code
            output["ERRORS"] = validator.errors
        else:
            output["STATUS"] = "Bad Requst"
            output["STATUS_CODE"] = 400
            output["ERRORS"] = validator.errors

    return output


# Generic output creation
def create_generic_output(data = dict, output_name = str):
    variable_list = []
    black_list = ["status", "status_code"]

    for variable_key, variable_value in data.items():
        if variable_key not in black_list:
            variable_value = f"{variable_value}"

        variable_list.append({
            "VARIABLE_NAME": variable_key,
            "VARIABLE_VALUE": f"{variable_value}"
        })

    return {
        "CORRELATIONID": output_name,
        "VARIABLE_LIST": variable_list
    }


# Azure's data logging format
def format_az_log(log):
    log_df = pd.DataFrame(log, index=[0])
    result = ''

    if log_df.empty:
        pass
    else:
        cols = log_df.columns
        for i in range(len(cols)):
            if i == len(cols) - 1:
                result = result + f"{cols[i]}"
            else:
                result = result + f"{cols[i]},"

        for idx, row in log_df.iterrows():
            d = f"{row[0]}, {row[1]}, {row[2]}" #, {row[3]}, {row[4]}, {row[5]}, {row[6]}"
            result = result + "\n" + d
    return result


def create_errors_collection(code, errors, schemaValidationErrors):
    if isinstance(errors, str):  
        schemaValidationErrors.append(errors)
        return schemaValidationErrors
    for key, value in errors.items():
        mainVar = key
        for item in value:
            if isinstance(item, str):                 
                 scheValError = {"Code" : "SchemaValidationError", "Description": item + " : " + key}
                 schemaValidationErrors.append(scheValError)
            else:
                for key, value in item.items():
                    if len(str(key)) == 1:
                        for item in value:
                            for key, value in item.items():
                                childVar = key
                                desc = value[0]
                                description = f"{mainVar}.{childVar} {desc}"
                                scheValError = {"Code" : code, "Description": description}
                                schemaValidationErrors.append(scheValError)
                    else:
                        childVar = key
                        desc = value[0]
                        description = f"{mainVar}.{childVar} {desc}"
                        scheValError = {"Code" : code, "Description": description}
                        schemaValidationErrors.append(scheValError)
           
    return schemaValidationErrors

def create_azsql_engine(AZSQLDatabase):

    if AZSQLDatabase:
        db = AZSQLDatabase
    else:
        db = os.environ['AZSQLDatabase']       

    params = urllib.parse.quote_plus(
        'Driver=%s;' % os.environ['AZSQLDriver'] +
        'Server=tcp:%s,1433;' % os.environ['AZSQLServer'] +
        'Database=%s;' % db +
        'Uid=%s;' % os.environ['AZSQLUID'] +
        'Pwd={%s};' % os.environ['AZSQLPWD'] +
        'Encrypt=yes;' +
        'TrustServerCertificate=no;' +
        'Connection Timeout=30;')

    conn_str = 'mssql+pyodbc:///?odbc_connect=' + params
    engine = create_engine(conn_str) 

    return engine


def create_azsql_connection(AZSQLDatabase):    
    if AZSQLDatabase:
        db = AZSQLDatabase
    else:
        db = os.environ['AZSQLDatabase']

    return pyodbc.connect(
        DRIVER=os.environ['AZSQLDriver'],
        SERVER=os.environ['AZSQLServer'], #needs to have tcp: prefixed!
        PORT=os.environ['AZSQLPort'], #usually 1433
        DATABASE=db,
        UID=os.environ['AZSQLUID'],
        PWD=os.environ['AZSQLPWD']
    )

def create_azsql_engineazureauth(AZSQLDatabase):
    """
        Database Connection setup if AZSQLActiveDirectoryAuth is not set to 1
    """

    if AZSQLDatabase:
        db = AZSQLDatabase
    else:
        db = get_env_var('AZSQLDatabase')

    params = urllib.parse.quote_plus(
        'Driver=%s;' % get_env_var('AZSQLDriver') + 
        'Server=tcp:%s,1433;' % get_env_var('AZSQLServer') +
        'Database=%s;' % db +
        'Uid=%s;' % get_env_var('AZSQLUID') +
        'Pwd={%s};' % get_env_var('AZSQLPWD') +
        'Encrypt=yes;' +
        'TrustServerCertificate=no;' +
        'Connection Timeout=%s' % get_env_var('AZSQLConnectionTimeout'))
    
    conn_str = 'mssql+pyodbc:///?odbc_connect=' + params
    poolSize = get_env_var('AZSQLDatabasePoolSize') 
    PoolMaxOverflow = get_env_var('AZSQLDatabasePoolMaxOverflow')

    engine = create_engine(conn_str, pool_size=int(poolSize), max_overflow=int(PoolMaxOverflow),pool_pre_ping=True)
    return engine

def create_azsql_engine_activedirectoryauth(AZSQLDatabase):
    """
        Database Connection setup if AZSQLActiveDirectoryAuth is set to 1
    """

    if AZSQLDatabase:
        db = AZSQLDatabase
    else:
        db = get_env_var('AZSQLDatabase')     
    params = urllib.parse.quote_plus(
        'Driver=%s;' % get_env_var('AZSQLDriver') +
        'Server=tcp:%s,1433;' % get_env_var('AZSQLServer') +
        'DATABASE=%s;' % db +
        'UID=%s;' % get_env_var('AZSQLUID') +
        'PWD={%s};' % get_env_var('AZSQLPWD') +
        'Authentication=ActiveDirectoryPassword;' +
        'Connection Timeout=%s' % get_env_var('AZSQLConnectionTimeout'))

    conn_str = 'mssql+pyodbc:///?odbc_connect=' + params
    poolSize = get_env_var('AZSQLDatabasePoolSize') 
    PoolMaxOverflow = get_env_var('AZSQLDatabasePoolMaxOverflow')

    engine = create_engine(conn_str, pool_size=int(poolSize), max_overflow=int(PoolMaxOverflow),pool_pre_ping=True)
    return engine


# use this locally if you want to enable logging,
def log_sql_alchemy(logYN):
    if logYN:
        # configure logging
        logging.basicConfig()
        logger = logging.getLogger("sqlalchemy.engine")
        logger.setLevel(logging.INFO)

        # create file handler and set level to INFO
        handler = logging.FileHandler("sqlalchemy.log")
        handler.setLevel(logging.INFO)

        # create formatter
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)

        # add handler to logger
        logger.addHandler(handler)


# Check if variable is in cache, otherwise get it from environment.
def get_env_var(name):
    if name in env_cache:
        return env_cache.get(name)
    value = os.getenv(name)
    env_cache.set(name, value)
    return value


def create_sf_engine():
    return create_engine(URL(
    account = get_env_var("SnowflakeAccount"),
    user = get_env_var("SnowflakeUser"),
    password = get_env_var("SnowflakePassword"),
    database = get_env_var("SnowflakeDB"),
    schema = get_env_var("SnowflakeSchema"),
    warehouse = get_env_var("SnowflakeWH"),
    role = get_env_var("SnowflakeRole"),
    ))