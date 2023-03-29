#include "schedule_utils.h"

#include "sop_payload_utils.h"
#include "sop_topic_utils.h"
#include "CAPString.h"
#include "db_handler.h"
#include "mqtt_message_handler.h"
#include "task.h"
#include "utils.h"

//----------------------------------------
// Util Methods
//----------------------------------------

cap_result ScheduleUtils_AssignExecutionResult(IN cap_handle hVariableHash, IN cap_handle hOutputList,
                                               IN SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strVariableName = NULL;
  SExpression *pstVariableExp = NULL;
  int nLen = 0;

  result = CAPLinkedList_GetLength(hOutputList, &nLen);
  ERRIFGOTO(result, _EXIT);

  if (nLen > 1) {
    SOPLOG_WARN("Multiple Return is not supported. Will use only the first one...");
  }

  result = CAPLinkedList_Get(hOutputList, LINKED_LIST_OFFSET_FIRST, 0, (void **)&strVariableName);
  ERRIFGOTO(result, _EXIT);

  result = CAPHash_GetDataByKey(hVariableHash, strVariableName, (void **)&pstVariableExp);
  ERRIFGOTO(result, _EXIT);

  pstVariableExp->enType = MapValueTypeToExpressionType(pstExecutionResult->enType);

  if (pstVariableExp->enType == EXP_TYPE_BINARY || pstVariableExp->enType == EXP_TYPE_STRING) {
    if (pstVariableExp->strStringValue == NULL) pstVariableExp->strStringValue = CAPString_New();
    result = CAPString_Set(pstVariableExp->strStringValue, pstExecutionResult->strStringValue);
    ERRIFGOTO(result, _EXIT);
  } else {
    pstVariableExp->dbValue = pstExecutionResult->dbValue;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static CALLBACK cap_result ApplySuperScheduleResult(IN cap_string strScheduleKey, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScheduleInfo *pstScheduleInfo = NULL;
  SScheduleResult *pstScheduleResult = NULL;
  cap_string strPrimaryIdentifier = NULL;
  cap_string strServiceName = NULL;
  cap_string strThingName = NULL;
  int nLen = -1;
  cap_bool bFound = FALSE;

  pstScheduleInfo = (SScheduleInfo *)pData;
  pstScheduleResult = (SScheduleResult *)pUserData;

  if (pstScheduleInfo->enState == SCHEDULE_STATE_DONE) {
    result = ERR_CAP_NOERROR;
    goto _EXIT;
  }

  result = ParseScheduleKey(strScheduleKey, &strPrimaryIdentifier, &strServiceName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(pstScheduleInfo->hMappedThingNameList, &nLen);
  ERRIFGOTO(result, _EXIT);

  bFound = FALSE;
  for (int i = 0; i < nLen; i++) {
    result =
        CAPLinkedList_Get(pstScheduleInfo->hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strThingName);
    ERRIFGOTO(result, _EXIT);

    if (CAPString_IsEqual(pstScheduleResult->strThingName, strThingName) == TRUE) {
      bFound = TRUE;
      break;
    }
  }

  if (bFound) {
    SOPLOG_DEBUG("Schedule Info %s is SCHEDULE_STATE_DONE now: %s", CAPString_LowPtr(strScheduleKey, NULL),
                 CAPString_LowPtr(strThingName, NULL));
    pstScheduleInfo->enState = SCHEDULE_STATE_DONE;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strPrimaryIdentifier);
  SAFE_CAPSTRING_DELETE(strServiceName);
  return result;
}

cap_result ScheduleUtils_ApplySuperScheduleResult(cap_handle hScheduleTable, cap_string strScenarioName,
                                                  SScheduleResult *pstScheduleResult) {
  cap_result result = ERR_CAP_UNKNOWN;

  result = ScheduleTable_TraverseScenario(hScheduleTable, strScenarioName, ApplySuperScheduleResult, pstScheduleResult);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static CALLBACK cap_result InitServiceTraverse(IN cap_string strScheduleKey, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  SServiceInfo *pstServiceInfo = NULL;
  SScheduleInfo *pstScheduleInfo = NULL;
  MySchedulingPolicies *pstContext = NULL;
  cap_handle hValueCache = NULL;
  cap_handle hMQTTHandler = NULL;
  cap_string strPrimaryIdentifier = NULL;
  cap_string strServiceName = NULL;
  cap_string strThingName = NULL;
  cap_string strTargetMiddlewareName = NULL;
  cap_string strServiceKey = NULL;
  cap_string strTopic = NULL;
  int nLen = -1;

  pstScheduleInfo = (SScheduleInfo *)pData;
  pstContext = (MySchedulingPolicies *)pUserData;

  strTopic = CAPString_New();
  ERRMEMGOTO(strTopic, result, _EXIT);

  strServiceKey = CAPString_New();
  ERRMEMGOTO(strServiceKey, result, _EXIT);

  strTargetMiddlewareName = CAPString_New();
  ERRMEMGOTO(strTargetMiddlewareName, result, _EXIT);

  result = ParseScheduleKey(strScheduleKey, &strPrimaryIdentifier, &strServiceName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(pstScheduleInfo->hMappedThingNameList, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    result =
        CAPLinkedList_Get(pstScheduleInfo->hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strThingName);
    ERRIFGOTO(result, _EXIT);

    // Init a Value
    if (pstScheduleInfo->enServiceType == SERVICE_TYPE_VALUE) {
      // pass
    }
    // Init a Function
    // subscribe execution request topic
    else if (pstScheduleInfo->enServiceType == SERVICE_TYPE_FUNCTION) {
      result = ServiceTable_Get(pstContext->hServiceTable_, strThingName, strServiceName, &pstServiceInfo);
      ERRIFGOTO(result, _EXIT);

      if (pstServiceInfo->bIsSuper == TRUE) {
        result = DBHandler_GetMiddlewareNameBySuperThingName(strThingName, strTargetMiddlewareName);
        ERRIFGOTO(result, _EXIT);

        if (CAPString_IsEqual(strTargetMiddlewareName, pstContext->strMiddlewareName_) == TRUE) {
          result = GenerateExecutionResultTopic(CAPSTR_PROTOCOL_SM, strServiceName, strThingName,
                                                strTargetMiddlewareName, pstContext->strMiddlewareName_, strTopic);
          ERRIFGOTO(result, _EXIT);
        } else {
          result = GenerateExecutionResultTopic(CAPSTR_PROTOCOL_PC, strServiceName, strThingName,
                                                strTargetMiddlewareName, pstContext->strMiddlewareName_, strTopic);
          ERRIFGOTO(result, _EXIT);
        }
        if (pstContext->hParentMQTTHandler_ != NULL) {
          result = MqttMessageHandler_Subscribe(pstContext->hParentMQTTHandler_, strTopic);
          ERRIFGOTO(result, _EXIT);
        }
      } else {
        result = GenerateExecutionResultTopic(CAPSTR_PROTOCOL_TM, strServiceName, strThingName, NULL, NULL, strTopic);
        ERRIFGOTO(result, _EXIT);

        result = MqttMessageHandler_Subscribe(pstContext->hChildMQTTHandler_, strTopic);
        ERRIFGOTO(result, _EXIT);
      }

      SOPLOG_DEBUG("[Scheduler] Subscribe Topic --- %s", CAPString_LowPtr(strTopic, NULL));
    } else {
      ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strTopic);
  SAFE_CAPSTRING_DELETE(strServiceKey);
  SAFE_CAPSTRING_DELETE(strPrimaryIdentifier);
  SAFE_CAPSTRING_DELETE(strServiceName);
  SAFE_CAPSTRING_DELETE(strTargetMiddlewareName);
  return result;
}

cap_result ScheduleUtils_IntializeScenario(cap_handle hScheduleTable, cap_string strScenarioName,
                                           MySchedulingPolicies *pstContext) {
  cap_result result = ERR_CAP_UNKNOWN;

  // FIXME: determine how to subscribe
  // result = ScheduleTable_TraverseScenario(hScheduleTable, strScenarioName, InitServiceTraverse, pstContext);
  // ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

CALLBACK static cap_result FindThing(IN cap_string strScheduleKey, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScheduleInfo *pstScheduleInfo = NULL;
  SGetAffectedScenarioOnUnregUserData *pstUserData;
  cap_string strThingName = NULL;
  int nLen = -1;

  pstScheduleInfo = (SScheduleInfo *)pData;
  pstUserData = (SGetAffectedScenarioOnUnregUserData *)pUserData;

  result = CAPLinkedList_GetLength(pstScheduleInfo->hMappedThingNameList, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    result =
        CAPLinkedList_Get(pstScheduleInfo->hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strThingName);
    ERRIFGOTO(result, _EXIT);

    if (CAPString_IsEqual(strThingName, pstUserData->strThingName) == TRUE) {
      pstUserData->bFound = TRUE;
      break;
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

CALLBACK static cap_result GetAffectedScenarioOnUnreg(IN cap_string strScenarioName, IN void *pData,
                                                      IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScenarioInfo *pstScenarioInfo = NULL;
  SGetAffectedScenarioOnUnregUserData *pstUserData;
  cap_handle hServiceScheduleInfoHash = NULL;
  cap_string strScenarioNameCopy = NULL;

  pstScenarioInfo = (SScenarioInfo *)pData;
  pstUserData = (SGetAffectedScenarioOnUnregUserData *)pUserData;
  pstUserData->strScenarioNameRef = strScenarioName;
  pstUserData->bFound = FALSE;

  result =
      ScheduleTable_TraverseScenario(pstUserData->pstContext->hScheduleTable_, strScenarioName, FindThing, pstUserData);
  ERRIFGOTO(result, _EXIT);

  if (pstUserData->bFound == TRUE) {
    strScenarioNameCopy = CAPString_New();
    ERRMEMGOTO(strScenarioNameCopy, result, _EXIT);

    result = CAPString_Set(strScenarioNameCopy, strScenarioName);
    ERRIFGOTO(result, _EXIT);

    result = CAPLinkedList_Add(pstUserData->hScenarioNameList, LINKED_LIST_OFFSET_LAST, 0, strScenarioNameCopy);
    ERRIFGOTO(result, _EXIT);

    // this string will be freed on the destroy linked list
    strScenarioNameCopy = NULL;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// cap_result ScheduleUtils_GetAffectedScenarioOnReg(MySchedulingPolicies *pstContext, cap_string strThingName,
//                                                     cap_handle *phScenarioNameList) {
//   cap_result result = ERR_CAP_UNKNOWN;
//   SGetAffectedScenarioOnUnregUserData stUserData;

//   stUserData.pstContext = pstContext;
//   stUserData.strThingName = strThingName;
//   result = CAPLinkedList_Create(&(stUserData.hScenarioNameList));
//   ERRIFGOTO(result, _EXIT);

//   result = ScenarioTable_Traverse(pstContext->hScenarioTable_, GetAffectedScenarioOnReg, &stUserData);
//   ERRIFGOTO(result, _EXIT);

//   *phScenarioNameList = stUserData.hScenarioNameList;

//   result = ERR_CAP_NOERROR;
// _EXIT:
//   if (result != ERR_CAP_NOERROR) {
//     if (stUserData.hScenarioNameList != NULL) {
//       result = CAPLinkedList_Traverse(stUserData.hScenarioNameList, DestroyStringList, NULL);
//       result = CAPLinkedList_Destroy(&(stUserData.hScenarioNameList));
//     }
//   }
//   return result;
// }

cap_result ScheduleUtils_GetAffectedScenarioOnUnreg(MySchedulingPolicies *pstContext, cap_string strThingName,
                                                    cap_handle *phScenarioNameList) {
  cap_result result = ERR_CAP_UNKNOWN;
  SGetAffectedScenarioOnUnregUserData stUserData;

  stUserData.pstContext = pstContext;
  stUserData.strThingName = strThingName;
  result = CAPLinkedList_Create(&(stUserData.hScenarioNameList));
  ERRIFGOTO(result, _EXIT);

  result = ScenarioTable_Traverse(pstContext->hScenarioTable_, GetAffectedScenarioOnUnreg, &stUserData);
  ERRIFGOTO(result, _EXIT);

  *phScenarioNameList = stUserData.hScenarioNameList;

  result = ERR_CAP_NOERROR;
_EXIT:
  if (result != ERR_CAP_NOERROR) {
    if (stUserData.hScenarioNameList != NULL) {
      result = CAPLinkedList_Traverse(stUserData.hScenarioNameList, DestroyStringList, NULL);
      result = CAPLinkedList_Destroy(&(stUserData.hScenarioNameList));
    }
  }
  return result;
}

cap_result ScheduleUtils_GetAffectedScenarioOnCancel(MySchedulingPolicies *pstContext, cap_string strScenarioName,
                                                     cap_handle *phScenarioNameList) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hScheduleMap = NULL;

  result = ScheduleTable_GetScheduleMap(pstContext->hScheduleTable_, strScenarioName, &hScheduleMap);
  ERRIFGOTO(result, _EXIT);

  // *phScenarioNameList = stUserData.hScenarioNameList;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static cap_result FindBestThing(IN cap_handle hCandidateList, IN EServiceType enServiceType,
                                IN cap_string strScenarioName, IN OUT cap_string strPickedThingName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strThingName = NULL;
  int targetIdx = -1;
  int nLen = 0;

  IFVARERRASSIGNGOTO(hCandidateList, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strScenarioName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strPickedThingName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_GetLength(hCandidateList, &nLen);
  ERRIFGOTO(result, _EXIT);

  if (nLen == 0) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  SOPLOG_DEBUG("Find the best thing with schedule info: %s", CAPString_LowPtr(strScenarioName, NULL));

  targetIdx = (int)(rand() % nLen);  // random (temporal policies)

  result = CAPLinkedList_Get(hCandidateList, LINKED_LIST_OFFSET_FIRST, targetIdx, (void **)&strThingName);
  ERRIFGOTO(result, _EXIT);

  result = CAPString_Set(strPickedThingName, strThingName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static cap_result MapServiceToThings(IN MySchedulingPolicies *pstContext, cap_string strServiceName,
                                     IN cap_handle hCandidateList, IN ERangeType enRangeType,
                                     IN EServiceType enServiceType, IN cap_string strScenarioName,
                                     IN OUT cap_handle hMappedThingNameList) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strPickedThingName = NULL;

  // clear the previous mapping
  if (hMappedThingNameList != NULL) {
    CAPLinkedList_Traverse(hMappedThingNameList, DestroyStringList, NULL);
    CAPLinkedList_Clear(hMappedThingNameList);
  }

  if ((enServiceType == SERVICE_TYPE_FUNCTION && enRangeType == RANGE_TYPE_ALL) ||
      (enServiceType == SERVICE_TYPE_VALUE && enRangeType == RANGE_TYPE_OR)) {
    result = CAPLinkedList_Duplicate(hMappedThingNameList, hCandidateList, DuplicateStringList, NULL);
    ERRIFGOTO(result, _EXIT);
  } else if ((enServiceType == SERVICE_TYPE_FUNCTION && enRangeType == RANGE_TYPE_NONE) ||
             (enServiceType == SERVICE_TYPE_VALUE && enRangeType == RANGE_TYPE_NONE)) {
    // pick a candidate following a scheduling policies
    strPickedThingName = CAPString_New();
    ERRMEMGOTO(strPickedThingName, result, _EXIT);

    result = pstContext->OnMapService(strServiceName, hCandidateList, &strPickedThingName);
    ERRIFGOTO(result, _EXIT);

    result = CAPLinkedList_Add(hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, 0, strPickedThingName);
    ERRIFGOTO(result, _EXIT);

    // this will be freed on hMappedThingNameList destroy.
    strPickedThingName = NULL;
  } else {
    ERRASSIGNGOTO(result, ERR_CAP_NOT_SUPPORTED, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static cap_result RequestSuperServiceSchedule(IN cap_string strServiceName, IN cap_string strScenarioName,
                                              IN cap_string strMyMiddlewareName, IN cap_handle hRunQueue,
                                              IN int nPeriodMs, IN SScheduleInfo *pstScheduleInfo) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strTargetMiddlewareName = NULL;
  cap_string strSuperThingName = NULL;
  SRunTask *pstRunTask = NULL;

  int nLen = 0;

  IFVARERRASSIGNGOTO(strServiceName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strScenarioName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(pstScheduleInfo, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  SOPLOG_DEBUG("RequestSuperServiceSchedule %s", CAPString_LowPtr(strServiceName, NULL));

  strTargetMiddlewareName = CAPString_New();
  ERRMEMGOTO(strTargetMiddlewareName, result, _EXIT);

  // exception handling
  result = CAPLinkedList_GetLength(pstScheduleInfo->hMappedThingNameList, &nLen);
  ERRIFGOTO(result, _EXIT);

  if (nLen == 0 || nLen > 1) {
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  }

  // get target super thing name
  result = CAPLinkedList_Get(pstScheduleInfo->hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, 0,
                             (void **)&strSuperThingName);
  ERRIFGOTO(result, _EXIT);

  // get target middleware name
  result = DBHandler_GetMiddlewareNameBySuperThingName(strSuperThingName, strTargetMiddlewareName);
  ERRIFGOTO(result, _EXIT);

  result = RunTask_Create(SUPER_SCHEDULE_BY_SCENARIO, &pstRunTask);
  ERRIFGOTO(result, _EXIT);

  if (CAPString_IsEqual(strTargetMiddlewareName, strMyMiddlewareName) == TRUE) {
    // MS/SCHEDULE/[SuperFunctionName]/[SuperThingName]/[MiddlewareName]/[RequesterMWName]
    result = GenerateScheduleRequestTopic(CAPSTR_PROTOCOL_MS, strServiceName, strSuperThingName,
                                          strTargetMiddlewareName, strMyMiddlewareName, pstRunTask->strRunTopic);
    ERRIFGOTO(result, _EXIT);

    // SM/RESULT/SCHEDULE/[SuperFunctionName]/[SuperThingName]/[MiddlewareName]/[RequesterMWName]
    result = GenerateScheduleResultTopic(CAPSTR_PROTOCOL_SM, strServiceName, strSuperThingName, strTargetMiddlewareName,
                                         strMyMiddlewareName, pstRunTask->strResultTopic);
    ERRIFGOTO(result, _EXIT);
  } else {
    // CP/SCHEDULE/[SuperFunctionName]/[SuperThingName]/[MiddlewareName]/[RequesterMWName]
    result = GenerateScheduleRequestTopic(CAPSTR_PROTOCOL_CP, strServiceName, strSuperThingName,
                                          strTargetMiddlewareName, strMyMiddlewareName, pstRunTask->strRunTopic);
    ERRIFGOTO(result, _EXIT);

    // PC/RESULT/SCHEDULE/[SuperFunctionName]/[SuperThingName]/[MiddlewareName]/[RequesterMWName]
    result = GenerateScheduleResultTopic(CAPSTR_PROTOCOL_PC, strServiceName, strSuperThingName, strTargetMiddlewareName,
                                         strMyMiddlewareName, pstRunTask->strResultTopic);
    ERRIFGOTO(result, _EXIT);
  }

  result = GenerateScheduleRequestPayload(strScenarioName, nPeriodMs, pstRunTask->strPayload);
  ERRIFGOTO(result, _EXIT);

  SOPLOG_DEBUG("Put Super Service Schedule Request to RunQueue %s", CAPString_LowPtr(strServiceName, NULL));

  result = CAPQueue_Put(hRunQueue, pstRunTask);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strTargetMiddlewareName);

  return result;
}

static CALLBACK cap_result ScheduleService(IN cap_string strScheduleKey, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hTempCandidateList = NULL;
  cap_handle hCandidateList = NULL;
  cap_handle hTagList = NULL;
  ERangeType enRangeType = RANGE_TYPE_NONE;
  cap_string strPrimaryIdentifier = NULL;
  cap_string strThingName = NULL;
  cap_string strServiceName = NULL;
  cap_string strScenarioName = NULL;
  cap_string strNewThingName = NULL;
  SScheduleInfo *pstScheduleInfo = NULL;
  SScheduleServiceUserData *pstUserData = NULL;
  int nLen = 0;
  int nPeriodMs = -1;
  long long llExecTimeMs = -1;
  cap_bool bIsSuper = -1;
  EServiceState enState = SERVICE_STATE_READY;

  pstScheduleInfo = (SScheduleInfo *)pData;
  pstUserData = (SScheduleServiceUserData *)pUserData;
  strScenarioName = pstUserData->strScenarioName;

  result = CAPLinkedList_Create(&hTempCandidateList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Create(&hCandidateList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Create(&hTagList);
  ERRIFGOTO(result, _EXIT);

  // SOPLOG_DEBUG("Schedule %s", CAPString_LowPtr(strScheduleKey, NULL));

  result = ParseScheduleKey(strScheduleKey, &strPrimaryIdentifier, &strServiceName);
  ERRIFGOTO(result, _EXIT);

  result = ParsePrimaryIdentifier(strPrimaryIdentifier, &enRangeType, hTagList);
  ERRIFGOTO(result, _EXIT);

  result = DBHandler_GetCandidateList(hTagList, strServiceName, pstScheduleInfo->enServiceType, hTempCandidateList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(hTempCandidateList, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    cap_bool bSchedulable = FALSE;

    result = CAPLinkedList_Get(hTempCandidateList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strThingName);
    ERRIFGOTO(result, _EXIT);

    result = ServiceTable_GetState(pstUserData->pstContext->hServiceTable_, strThingName, strServiceName, &enState);
    ERRIFGOTO(result, _EXIT);

    // skip the services with error state
    if (enState == SERVICE_STATE_ERROR) {
      continue;
    }

    result =
        ServiceTable_GetExecTime(pstUserData->pstContext->hServiceTable_, strThingName, strServiceName, &llExecTimeMs);
    ERRIFGOTO(result, _EXIT);

    result = ServiceTable_GetIsSuper(pstUserData->pstContext->hServiceTable_, strThingName, strServiceName, &bIsSuper);
    ERRIFGOTO(result, _EXIT);

    // Note: assume that every cadidate has the same service property
    // super service with ALL/OR range is not supported.
    if ((bIsSuper == TRUE && enRangeType == RANGE_TYPE_ALL) || (bIsSuper == TRUE && enRangeType == RANGE_TYPE_OR)) {
      SOPLOG_DEBUG("SKIP... super service with ALL/OR range is not supported.");
      continue;
    }

    result = ScenarioTable_GetPeriod(pstUserData->hCurScenarioTable, strScenarioName, &nPeriodMs);
    ERRIFGOTO(result, _EXIT);

    if (bIsSuper) {
      bSchedulable = TRUE;  // Assume Super Service is always available
    } else {
      SOPLOG_DEBUG("ScheduleService - CheckSchedulability %s", CAPString_LowPtr(strThingName, NULL));

      result = ScheduleUtils_CheckSchedulability(pstUserData->pstContext->hScheduleTable_,
                                                 pstUserData->pstContext->hScenarioTable_,
                                                 pstUserData->pstContext->hServiceTable_, strThingName, strServiceName,
                                                 llExecTimeMs, nPeriodMs, &bSchedulable);
      ERRIFGOTO(result, _EXIT);
    }

    if (bSchedulable) {
      strNewThingName = CAPString_New();

      result = CAPString_Set(strNewThingName, strThingName);
      ERRIFGOTO(result, _EXIT);

      // SOPLOG_DEBUG("Add %s to hCandidateList", CAPString_LowPtr(strNewThingName, NULL));

      result = CAPLinkedList_Add(hCandidateList, LINKED_LIST_OFFSET_FIRST, 0, strNewThingName);
      ERRIFGOTO(result, _EXIT);
    } else {
      // SOPLOG_DEBUG("Exclude %s from hCandidateList", CAPString_LowPtr(strThingName, NULL));
    }
  }

  result = CAPLinkedList_GetLength(hCandidateList, &nLen);
  ERRIFGOTO(result, _EXIT);

  if (nLen == 0) {
    SOPLOG_ERROR("Candidate nLen: %d", nLen);
    result = ScenarioTable_SetState(pstUserData->hCurScenarioTable, strScenarioName, SCENARIO_STATE_STUCKED);
    ERRIFGOTO(result, _EXIT);

    pstScheduleInfo->enState = SCHEDULE_STATE_ERROR;
  } else {
    // The mapped things will be put in pstScheduleInfo->hMappedThingList
    result = MapServiceToThings(pstUserData->pstContext, strServiceName, hCandidateList, enRangeType,
                                pstScheduleInfo->enServiceType, strScenarioName, pstScheduleInfo->hMappedThingNameList);
    ERRIFGOTO(result, _EXIT);

    // request a super service schedule *Asynchronously*
    if (bIsSuper == TRUE) {
      result = ScenarioTable_SetState(pstUserData->hCurScenarioTable, strScenarioName, SCENARIO_STATE_SCHEDULING);
      ERRIFGOTO(result, _EXIT);

      result = RequestSuperServiceSchedule(strServiceName, strScenarioName, pstUserData->pstContext->strMiddlewareName_,
                                           pstUserData->pstContext->hRunQueue_, nPeriodMs, pstScheduleInfo);
      ERRIFGOTO(result, _EXIT);

      pstScheduleInfo->enState = SCHEDULE_STATE_READY;
    } else {
      pstScheduleInfo->enState = SCHEDULE_STATE_DONE;
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hTempCandidateList != NULL) {
    CAPLinkedList_Traverse(hTempCandidateList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hTempCandidateList);
  }

  if (hCandidateList != NULL) {
    CAPLinkedList_Traverse(hCandidateList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hCandidateList);
  }

  if (hTagList != NULL) {
    CAPLinkedList_Traverse(hTagList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hTagList);
  }

  SAFE_CAPSTRING_DELETE(strPrimaryIdentifier);
  SAFE_CAPSTRING_DELETE(strServiceName);
  return result;
}

cap_result ScheduleUtils_ScheduleScenario(MySchedulingPolicies *pstContext, cap_string strScenarioName) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScheduleServiceUserData stUserData;

  SOPLOG_DEBUG("[ScheduleUtils] ScheduleScenario %s", CAPString_LowPtr(strScenarioName, NULL));

  stUserData.strScenarioName = CAPString_New();
  stUserData.pstContext = pstContext;
  stUserData.hCurScenarioTable = pstContext->hTempScenarioTable_;

  result = CAPString_Set(stUserData.strScenarioName, strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = ScheduleTable_TraverseScenario(pstContext->hTempScheduleTable_, stUserData.strScenarioName, ScheduleService,
                                          &stUserData);
  if (result != ERR_CAP_NOERROR) {
    SOPLOG_WARN("%s ScheduleService error %d", CAPString_LowPtr(stUserData.strScenarioName, NULL), result);
    CAPASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(stUserData.strScenarioName);
  return result;
}

cap_result ScheduleUtils_UpdateScenario(MySchedulingPolicies *pstContext, cap_string strScenarioName,
                                        cap_bool *pbScheduled) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScheduleServiceUserData stUserData;

  stUserData.strScenarioName = strScenarioName;
  stUserData.pstContext = pstContext;
  stUserData.hCurScenarioTable = pstContext->hScenarioTable_;

  result = ScheduleTable_TraverseScenario(pstContext->hScheduleTable_, strScenarioName, ScheduleService, &stUserData);
  if (result != ERR_CAP_NOERROR) {
    SOPLOG_WARN("%s ScheduleService FAILED %d", CAPString_LowPtr(strScenarioName, NULL), result);
    *pbScheduled = FALSE;
  } else {
    SOPLOG_DEBUG("%s ScheduleService SUCCESS. result: %d", CAPString_LowPtr(strScenarioName, NULL), result);
    *pbScheduled = TRUE;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

static CALLBACK cap_result CheckAllScheduled(IN cap_string strScheduleKey, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strScenarioName = NULL;
  SScheduleInfo *pstScheduleInfo = NULL;
  cap_bool *pbAllScheduled;

  IFVARERRASSIGNGOTO(strScheduleKey, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(pData, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  pstScheduleInfo = (SScheduleInfo *)pData;
  pbAllScheduled = (cap_bool *)pUserData;

  if (pstScheduleInfo->enState == SCHEDULE_STATE_READY || pstScheduleInfo->enState == SCHEDULE_STATE_ERROR) {
    SOPLOG_DEBUG("%s is not scheduled", CAPString_LowPtr(strScheduleKey, NULL));
    *pbAllScheduled = FALSE;
  } else {
    SOPLOG_DEBUG("%s is scheduled", CAPString_LowPtr(strScheduleKey, NULL));
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result ScheduleUtils_CheckScenarioScheduled(cap_handle hScheduleTable, cap_string strScenarioName,
                                                cap_bool *pbAllScheduled) {
  cap_result result = ERR_CAP_UNKNOWN;

  result = ScheduleTable_TraverseScenario(hScheduleTable, strScenarioName, CheckAllScheduled, pbAllScheduled);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result ScheduleUtils_CheckSchedulability(IN cap_handle hScheduleTable, IN cap_handle hScenarioTable,
                                             IN cap_handle hServiceTable, IN cap_string strThingName,
                                             IN cap_string strFunctionName, IN long long llExecTimeMs, IN int nPeriodMs,
                                             OUT cap_bool *pbSchedulable) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bSchedulable = FALSE;
  cap_bool bIsParallel = FALSE;
  double dbCurrUtilization = 0.0;
  double dbReqUtilization = 0.0;
  SOPLOG_DEBUG("CheckSchedulability - llExecTimeMs %lld, nPeriodMs %d", llExecTimeMs, nPeriodMs);

  IFVARERRASSIGNGOTO(strThingName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strFunctionName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  // always ok if is parallel
  result = ServiceTable_GetIsParallel(hServiceTable, strThingName, strFunctionName, &bIsParallel);
  ERRIFGOTO(result, _EXIT);

  if (bIsParallel == TRUE) {
    *pbSchedulable = TRUE;
    goto _EXIT;
  }

  result = ScheduleTable_CurrUtilization(hScheduleTable, hScenarioTable, hServiceTable, strThingName, strFunctionName,
                                         &dbCurrUtilization);
  ERRIFGOTO(result, _EXIT);

  dbReqUtilization = (double)llExecTimeMs / nPeriodMs;

  if (dbReqUtilization + dbCurrUtilization <= (double)1.0) {
    bSchedulable = TRUE;
  } else {
    bSchedulable = FALSE;
  }

  SOPLOG_DEBUG("%s.%s - Current Util: %.2lf / Required Util: %.2lf ==> %s", CAPString_LowPtr(strThingName, NULL),
               CAPString_LowPtr(strFunctionName, NULL), dbCurrUtilization, dbReqUtilization,
               bSchedulable ? "Schedulable" : "Not Schedulable");

  *pbSchedulable = bSchedulable;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result ScheduleUtils_GetWaitingScenarioList(cap_handle hWaitQueue, cap_string strTargetThingName,
                                                cap_string strTargetServiceName, cap_handle *phScenarioList) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hScenarioList = NULL;
  int nLen = -1;
  SRunTask *pstRunTask = NULL;
  cap_string strFunctionName = NULL;
  cap_string strThingName = NULL;
  cap_string strScenarioName = NULL;
  cap_string strScenarioNameToAdd = NULL;

  result = CAPLinkedList_Create(&hScenarioList);
  ERRMEMGOTO(hScenarioList, result, _EXIT);

  strFunctionName = CAPString_New();
  ERRMEMGOTO(strFunctionName, result, _EXIT);

  strThingName = CAPString_New();
  ERRMEMGOTO(strThingName, result, _EXIT);

  result = CAPQueue_GetLength(hWaitQueue, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    result = CAPQueue_Get(hWaitQueue, FALSE, (void **)&pstRunTask);
    if (result == ERR_CAP_NO_DATA) {
      result = ERR_CAP_NOERROR;
      break;
    }

    if (pstRunTask != NULL) {
      result = ParseExecutionRequestTopicString(pstRunTask->strRunTopic, strFunctionName, strThingName, NULL, NULL);
      ERRIFGOTO(result, _EXIT);

      result = ParseExecutionRequestPayloadString(pstRunTask->strPayload, &strScenarioName);
      ERRIFGOTO(result, _EXIT);

      if (CAPString_IsEqual(strThingName, strTargetThingName) == TRUE &&
          CAPString_IsEqual(strFunctionName, strTargetServiceName) == TRUE) {
        strScenarioNameToAdd = CAPString_New();
        ERRMEMGOTO(strScenarioNameToAdd, result, _EXIT);

        result = CAPString_Set(strScenarioNameToAdd, strScenarioName);
        ERRIFGOTO(result, _EXIT);

        result = CAPLinkedList_Add(hScenarioList, LINKED_LIST_OFFSET_LAST, 0, strScenarioNameToAdd);
        ERRIFGOTO(result, _EXIT);

        strScenarioNameToAdd = NULL;
      } else {
        // skip requesting.
        // it has been merged to the previous request.
        result = CAPQueue_Put(hWaitQueue, pstRunTask);
        ERRIFGOTO(result, _EXIT);
      }

      // do not free strScenarioName
      strScenarioName = NULL;
    }
  }

  *phScenarioList = hScenarioList;

  result = ERR_CAP_NOERROR;
_EXIT:
  if (result != ERR_CAP_NOERROR) {
    if (hScenarioList != NULL) {
      CAPLinkedList_Traverse(hScenarioList, DestroyStringList, NULL);
      CAPLinkedList_Destroy(&hScenarioList);
    }
  }
  return result;
}
