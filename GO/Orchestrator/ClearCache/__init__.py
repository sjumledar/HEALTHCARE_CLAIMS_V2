import logging

import azure.functions as func
from cacheout import Cache

from ..OrchestratorExhaustive.Data.Repository import cache


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        cache.clear()
        message = "Cache successfully cleared"
    except Exception as e:
        message = f"Error clearing Cache: {str(e)}"

    headers = {
        "Content-Type": "text/html"
    }

    return func.HttpResponse(
        message,
        headers=headers
    )

    
