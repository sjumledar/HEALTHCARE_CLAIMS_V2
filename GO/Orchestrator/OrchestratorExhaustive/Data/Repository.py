import logging
from numpy import empty
import pandas as pd
from ..Model.Metadata.OrchestratorIdentifier import OrchestratorIdentifier
from ..Model.Metadata.OrchestratorSummary import OrchestratorSummary
from ..Model.Metadata.ScoringOrchestratorSequencer import ScoringOrchestratorSequencer
from ..Model.Metadata.ScoringOrchestratorServiceContractInput import ScoringOrchestratorServiceContractInput
from ..Model.Metadata.ScoringOrchestratorServiceContractOutput import ScoringOrchestratorServiceContractOutput
from ..Model.Metadata.ServiceContract import ServiceContract
from ..Model.OrchUKRCCQSRequest import OrchUKRCCQSRequest
from ..Model.Entities.OrchUKRCCQSOutputDnBService import OrchUKRCCQSOutputDnBService
from ..Model.Entities.OrchUKRCCQSOutputDnBService import OrchUKRCCQSOldDnBService
from shared_code.helper_functions import *
from functools import lru_cache
from cacheout import Cache
cache = Cache()

#from cachetools import cached, LRUCache, TTLCache
# from diskcache import Cache
# cache = Cache()

#cache = Cache()

#@lru_cache(maxsize=256)
#@cache("FetchModelData")
#@cached(cache=LRUCache(maxsize=3200))
def FetchModelData(orchestratorIdentifier : OrchestratorIdentifier) :
    
    key = "ModelData:" + orchestratorIdentifier.ArchBusiness + orchestratorIdentifier.Coverage + orchestratorIdentifier.LineOfBusiness + str(orchestratorIdentifier.ScoringOrchestratorId) + (orchestratorIdentifier.TransType if orchestratorIdentifier.TransType!=None else "None" ) 
   
    if(key in cache):
         #result = cache[key]
         result = cache.get(key)
    else:
        logging.info('FetchModelData Started.')

        azsql = create_azsql_connection("SAMetadata")
        cur = azsql.cursor()

        sqlquery = """
            SELECT [AlgorithmId], 
            [AlgorithmVersion], 
            [AlgorithmName], 
            [AlgorithmDescription], 
            [LineOfBusiness], 
            [Coverage], 
            [TransType],  
            [AlgorithmStartDate], 
            [AlgorithmEndDate],  
            sea.[ScoringOrchestratorId]
            FROM ScoringOrchestrator se INNER JOIN ScoringOrchestratorAlgorithm sea
            ON se.ScoringOrchestratorId = sea.ScoringOrchestratorId
            WHERE se.ScoringOrchestratorId = {0}
            AND se.ArchBusiness = '{1}'
            AND sea.LineOfBusiness = '{2}'
            AND sea.Coverage = '{3}'
        """. format(
            orchestratorIdentifier.ScoringOrchestratorId,
            orchestratorIdentifier.ArchBusiness,
            orchestratorIdentifier.LineOfBusiness,
            orchestratorIdentifier.Coverage
        )

        results_df = pd.read_sql(sqlquery,azsql)
        result = OrchestratorSummary()

        for index, algo in results_df.iterrows():
            result.AlgorithmId = algo.AlgorithmId
            result.AlgorithmVersion = algo.AlgorithmVersion
            result.LineOfBusiness = algo.LineOfBusiness
            result.ScoreIdentifier = orchestratorIdentifier.ScoreIdentifier
            result.ScoringOrchestratorId = orchestratorIdentifier.ScoringOrchestratorId
            result.AlgorithmStartDate = algo.AlgorithmStartDate
            result.AlgorithmEndDate = algo.AlgorithmEndDate
            result.TransType = orchestratorIdentifier.TransType

            sqlVar = """
                SELECT distinct ServiceContractId, 
                ServiceContractName, 
                ServiceContractDescription, 
                ServiceContractCategory, 
                ScoringOrchestratorId, 
                ActiveStartDateTime, 
                ActiveEndDateTime, 
                ServiceKey,ServiceKeyType, 
                SecurityTokenKey,  
                IsDurableFunction,  
                DurableFunctionStatusURLField,  
                DurableFunctionStatusField,  
                DurableFunctionResultURLField,  
                DurableFunctionTimeoutInSeconds,  
                DurableFunctionRetryCount  
                FROM ScoringOrchestratorServiceContract sosc  
                WHERE sosc.[ScoringOrchestratorId] = {0}
            """.format(result.ScoringOrchestratorId)

            serviceResult_df = pd.read_sql(sqlVar, azsql)
            result.ServiceContracts = []

            for index, m in serviceResult_df.iterrows():
                sqlInput = """
                    SELECT AlgorithmId,
                    AlgorithmVersion,
                    ServiceContractId,
                    ServiceContractInputParameterName,
                    ServiceContractInputParameterDataType,
                    ServiceContractInputParameterSource,
                    ServiceContractInputParameterDefaultValue,
                    ServiceContractInputParameterDestination,
                    ServiceContractInputParameterMandatoryRule,
                    ModifiedDateTime,
                    ActiveStartDateTime,
                    ActiveEndDateTime,
                    ScoringOrchestratorId 
                    FROM ScoringOrchestratorServiceContractInput sosc
                    WHERE sosc.[AlgorithmId] = {0}
                    AND sosc.[AlgorithmVersion] = {1}
                    AND sosc.[ServiceContractId] = {2}
                    AND sosc.[ScoringOrchestratorId] = {3}
                """.format(
                    result.AlgorithmId,
                    result.AlgorithmVersion,
                    m.ServiceContractId,
                    result.ScoringOrchestratorId
                )

                scoringOrchestratorInputResults_df = pd.read_sql(sqlInput, azsql)
                m.ServiceContractInputs = []

                for index, i in scoringOrchestratorInputResults_df.iterrows():
                    m.ServiceContractInputs.append(i)

                sqlOutput = """
                    SELECT AlgorithmId, 
                    AlgorithmVersion, 
                    ServiceContractId, 
                    ServiceContractOutputParameterName, 
                    ServiceContractOutputParameterDataType, 
                    ServiceContractOutputParameterDestination, 
                    ModifiedDateTime, 
                    ActiveStartDateTime, 
                    ActiveEndDateTime, 
                    ScoringOrchestratorId  
                    FROM ScoringOrchestratorServiceContractOutput soso 
                    WHERE soso.[AlgorithmId] = {0}
                    AND soso.[AlgorithmVersion] = {1}
                    AND soso.[ServiceContractId] = {2} 
                    AND soso.[ScoringOrchestratorId] = {3}
                """.format(
                    result.AlgorithmId,
                    result.AlgorithmVersion,
                    m.ServiceContractId,
                    result.ScoringOrchestratorId
                )

                scoringOrchestratorOutputResults_df = pd.read_sql(sqlOutput, azsql)
                m.ServiceContractOutputs = []

                for index, o in scoringOrchestratorOutputResults_df.iterrows():
                    m.ServiceContractOutputs.append(o)

                result.ServiceContracts.append(m)
            
            sqlSeq = """
                SELECT ScoringOrchestratorId,
                SequencerName,
                SequencerCategory,
                SequencerOrder,
                ChildServiceContract, ActiveStartDateTime, ActiveEndDateTime
                FROM ScoringOrchestratorSequencer se 
                WHERE se.ScoringOrchestratorId = {0} ORDER BY SequencerOrder ASC
            """.format(orchestratorIdentifier.ScoringOrchestratorId)

            results1_df = pd.read_sql(sqlSeq, azsql)

            if not results1_df.empty:
                result.Sequencers = []
                for index, seq in results1_df.iterrows():
                    result.Sequencers.append(seq)
        
        # with Cache(cache.directory) as reference:
        #     reference.set(key, result)
        cache.set(key, result)
    return result

def GetOldDnBData(clientInfoInput, request : OrchUKRCCQSRequest):
    result = OrchUKRCCQSOldDnBService()
    logging.info('GetOldDnBData Started.')

    azsql = create_azsql_connection("SAOp")
    cur = azsql.cursor()

    sqlquery = """ SELECT OrchUKRCCQSOutputDnBServiceID,
    CorrelationID,DunsNumber,ConfidenceCode,
    CPCT,Error,AccountName,StreetAddress1,
    StreetAddress2,City,ZipCode,Country,
    Sourcesystem,OrchUKRCCQSInputScoreRequestID
    FROM OrchUKRCCQSOutputDnBService 
            WHERE 
            Error is null and DunsNumber is not null and ConfidenceCode is not null and
            OrchUKRCCQSInputScoreRequestID in( 
                SELECT max(sb.OrchUKRCCQSInputScoreRequestID) 
                FROM OrchUKRCCQSInputSubmission sb 
                INNER JOIN OrchUKRCCQSOutputDnBService odnb ON sb.OrchUKRCCQSInputScoreRequestID = odnb.OrchUKRCCQSInputScoreRequestID 
                WHERE sb.SubmissionNumber = '{0}'
                GROUP BY AccountName,StreetAddress1) and 
            AccountName = '{1}' and 
            StreetAddress1 = '{2}' and 
            StreetAddress2 = '{3}' and 
            City = '{4}' and             
            ZipCode = '{5}' and 
            Country = '{6}' and 
            Sourcesystem = '{7}' 
            ORDER BY OrchUKRCCQSOutputDnBServiceID DESC 
            """.format( 
                request.SubmissionInput.SubmissionNumber,
                request.ClientInfoInput.ClientName,
                request.ClientInfoInput.ClientLocationHouseNumberStreetName,
                request.ClientInfoInput.ClientLocationLocalityName,
                request.ClientInfoInput.ClientLocationTown,
                request.ClientInfoInput.ClientLocationPostalCode,
                request.ClientInfoInput.ClientLocationCountry,
                request.ScoreRequestInput.SourceSystem)

    results_df = pd.read_sql(sqlquery,azsql)
    
    for index, dnb in results_df.iterrows():
        logging.info("dnb found inside repository") 
        result.OrchUKRCCQSOutputDnBServiceID = dnb.OrchUKRCCQSOutputDnBServiceID
        result.CorrelationID  = dnb.CorrelationID
        result.DunsNumber = dnb.DunsNumber
        result.ConfidenceCode  = dnb.ConfidenceCode
        result.CPCT  = dnb.CPCT
        result.Error  = dnb.Error
        result.AccountName  = dnb.AccountName
        result.StreetAddress1  = dnb.StreetAddress1
        result.StreetAddress2  = dnb.StreetAddress2
        result.City  = dnb.City
        result.ZipCode  = dnb.ZipCode
        result.Country  = dnb.Country
        result.Sourcesystem  = dnb.Sourcesystem
        result.OrchUKRCCQSInputScoreRequestID  = dnb.OrchUKRCCQSInputScoreRequestID        
        return result
    return None