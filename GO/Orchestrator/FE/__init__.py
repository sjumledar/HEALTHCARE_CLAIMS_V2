import csv
import json
import logging
import os
import traceback
from datetime import datetime
from io import BytesIO
from shared_code import helper_functions 
import azure.functions as func
import pandas as pd


def main(
    req: func.HttpRequest,
    context: func.Context
    # SampleInputData: bytes,
    # ResultLog: func.Out[bytes]
    ) -> func.HttpResponse:

    logging.info('Python HTTP trigger function processed a request.')

    # initialize response variables
    out = {}
    output = {}
    status = "Success"
    status_code = 200
    error_msg = {}

    # log
    log = {}

    try:
        req_body = req.get_json()
    except:
        req_body = {}
    # output
    output = call_FE(req_body)
    headers = {
        "Content-Type": "application/json"
    }

    return func.HttpResponse(
        json.dumps(output),
        headers=headers
    )


def get_connection_saImplementation():
    try:
        global connection_saImplementation
        if (connection_saImplementation is None or connection_saImplementation.engine.engine._connection_cls._is_disconnect):    
            connection_saImplementation = helper_functions.create_azsql_engine(databasename) 
        return connection_saImplementation
    except Exception as e:
        traceback.print_exc()


def call_FE(req_body):
    logging.info('call_FE')
    logging.info('Python native call processed a FE request.')
    # initialize response variables
    generic_output = {}
    output = {}
    status = "Success"
    status_code = 200
    error_msg = {}

    # log
    log = {}
    azfoutput = {}
    try:
        logging.info(req_body)
        validation = helper_functions.validate_input(req_body)

        status = validation["STATUS"]
        status_code = validation["STATUS_CODE"]
        errors = validation["ERRORS"]
        error_msg = errors

        generic_output = exec_FE(status, status_code, error_msg, log, azfoutput, req_body)

        logging.info("exec_FE finished")
        logging.info(datetime.now())
    except Exception as e:
        logging.info(e)
        status_code = "fail"
        status = str(e)

    # output
    output["output"] = generic_output
    output["status"] = status
    output["status_code"] = status_code
    output["error_msg"] = error_msg

    return output


def exec_FE(status, status_code, error_msg, log, azfoutput, req_body):
    logging.info("exec_FE")
    logging.info(datetime.now())
    out = {}
    generic_output = {}
    try:
        if not error_msg:
            # conn = get_connection_saImplementation()
            CorrelationID = req_body["Submission"]["CorrelationID"]
            SubmissionNumber = req_body["Submission"]["SubmissionNumber"]
            # FE logic goes here
            # df = pd.read_sql(f"""SELECT * FROM ref.REF_DATA""", conn)
        else:
            CorrelationID = ""
            SubmissionNumber = ""

    except Exception as e:
        logging.info(e)
        error_msg["runtime_error"] = str(e)

    # function output
    out["SubmissionNumber"] = SubmissionNumber
    generic_output = helper_functions.create_generic_output(out, CorrelationID)
    logging.info("generic_output")

    return generic_output