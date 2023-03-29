// Algorithm with Energy Saving Policies
// - map services to the lowest energy-consuming things
// - merge exeuction

#include <CAPQueue.h>

#include "db_handler.h"
#include "jsonc_utils.h"
#include "mqtt_message_handler.h"
#include "my_scheduling_policies.h"
#include "scenario_table.h"
#include "schedule_table.h"
#include "schedule_utils.h"
#include "service_table.h"
CAPSTRING_CONST(CAPSTR_TO_SIMULATOR_FINISH, "SIM/FINISH");

static CALLBACK cap_result PrintStringList(IN int nOffset, IN void *pData, IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strString = NULL;

  strString = (cap_string)pData;

  if (strString != NULL) SOPLOG_DEBUG("[PrintStringList] %s", CAPString_LowPtr(strString, NULL));

  result = ERR_CAP_NOERROR;

  return result;
}

//----------------------------------------
// Member Methods
//----------------------------------------

cap_result MySchedulingPolicies::OnMapService(cap_string strServiceName, cap_handle hCandidateList,
                                          OUT cap_string *pstrMappedThingName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strThingName = NULL;
  cap_string strBestThingName = NULL;
  long long llMin = INT_MAX;
  SServiceInfo *pstServiceInfo = NULL;
  int nLen = 0;

  SOPLOG_DEBUG("OnMapService(%s)", CAPString_LowPtr(strServiceName, NULL));

  strBestThingName = CAPString_New();
  ERRMEMGOTO(strBestThingName, result, _EXIT);

  result = CAPLinkedList_GetLength(hCandidateList, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    result = CAPLinkedList_Get(hCandidateList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strThingName);
    ERRIFGOTO(result, _EXIT);

    result = ServiceTable_Get(this->hServiceTable_, strThingName, strServiceName, &pstServiceInfo);
    ERRIFGOTO(result, _EXIT);

    if (pstServiceInfo->llEnergyJ < llMin) {
      llMin = pstServiceInfo->llEnergyJ;
      result = CAPString_Set(strBestThingName, strThingName);
      ERRIFGOTO(result, _EXIT);

      SOPLOG_DEBUG("Update the Best Energy! Best Thing: %s", CAPString_LowPtr(strThingName, NULL));
    }
    // if (pstServiceInfo->llExecTimeMs < llMin) {
    //   llMin = pstServiceInfo->llExecTimeMs;
    //   result = CAPString_Set(strBestThingName, strThingName);
    //   ERRIFGOTO(result, _EXIT);

    //   SOPLOG_DEBUG("Update the Best Speed! Best Thing: %s", CAPString_LowPtr(strThingName, NULL));
    // }
  }

  *pstrMappedThingName = strBestThingName;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnScheduleScenarioCheck(cap_string strScenarioName, cap_bool *pbScheduled) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bAllScheduled = TRUE;

  SOPLOG_DEBUG("OnScheduleScenarioCheck(%s)", CAPString_LowPtr(strScenarioName, NULL));

  // 1. Schedule Services
  result = ScheduleUtils_ScheduleScenario(this, strScenarioName);
  ERRIFGOTO(result, _EXIT);

  // 2. Set state to INITALIZED if all services are scheduled.
  bAllScheduled = TRUE;
  result = ScheduleUtils_CheckScenarioScheduled(this->hTempScheduleTable_, strScenarioName, &bAllScheduled);
  ERRIFGOTO(result, _EXIT);

  if (bAllScheduled == TRUE) {
    *pbScheduled = TRUE;
  } else {
    *pbScheduled = FALSE;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnScheduleScenarioConfirm(cap_string strScenarioName) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScenarioInfo *pstScenarioInfo = NULL;
  cap_bool bScheduled = FALSE;
  cap_string strScenarioText = NULL;

  SOPLOG_DEBUG("OnScheduleScenarioConfirm(%s)", CAPString_LowPtr(strScenarioName, NULL));

  cap_handle hTempScheduleMap = NULL;
  cap_handle hNewScheduleMap = NULL;

  // Scenario Table Copy
  result = ScenarioTable_GetCopy(this->hTempScenarioTable_, strScenarioName, &pstScenarioInfo);
  ERRIFGOTO(result, _EXIT);

  result = ScenarioTable_Put(this->hScenarioTable_, strScenarioName, pstScenarioInfo->hScenarioModel,
                             pstScenarioInfo->nPriority);
  ERRIFGOTO(result, _EXIT);

  // Update Schedule Table's Mapped Thing List
  result = ScheduleTable_GetScheduleMap(this->hTempScheduleTable_, strScenarioName, &hTempScheduleMap);
  ERRIFGOTO(result, _EXIT);

  result = ScheduleMap_Copy(hTempScheduleMap, &hNewScheduleMap);
  ERRIFGOTO(result, _EXIT);

  result = ScheduleTable_AddScheduleMap(this->hScheduleTable_, strScenarioName, hNewScheduleMap);
  ERRIFGOTO(result, _EXIT);

  result = ScheduleTable_DeleteScheduleMap(this->hTempScheduleTable_, strScenarioName);
  ERRIFGOTO(result, _EXIT);

  // DB save
  strScenarioText = CAPString_New();
  ERRMEMGOTO(strScenarioText, result, _EXIT);

  result = AppScriptModeler_GetScenarioText(pstScenarioInfo->hScenarioModel, strScenarioText);
  ERRIFGOTO(result, _EXIT);

  result = DBHandler_AddScenario(strScenarioName, strScenarioText, pstScenarioInfo->nPriority);
  ERRIFGOTO(result, _EXIT);

  // Init Scenarios
  result = ScheduleUtils_IntializeScenario(this->hScheduleTable_, strScenarioName, this);
  ERRIFGOTO(result, _EXIT);

  result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_INITIALIZED);
  ERRIFGOTO(result, _EXIT);

  // Clean the copy
  result = ScenarioTable_Delete(this->hTempScenarioTable_, strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strScenarioText);
  return result;
}

cap_result MySchedulingPolicies::OnUpdateScenario(cap_string strScenarioName, cap_bool *pbScheduled) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScenarioInfo *pstScenarioInfo = NULL;
  cap_bool bScheduled = FALSE;
  cap_bool bAllScheduled = FALSE;

  SOPLOG_DEBUG("[SchedulingPolicies] OnUpdateScenario %s", CAPString_LowPtr(strScenarioName, NULL));

  result = ScheduleUtils_UpdateScenario(this, strScenarioName, &bScheduled);
  if (!bScheduled) {
    *pbScheduled = FALSE;
    SOPLOG_DEBUG("ScheduleUtils_UpdateScenario FAIL");

    result = ERR_CAP_NOERROR;
    goto _EXIT;
  }

  // 2. Set state to INITALIZED if all services are scheduled.
  bAllScheduled = TRUE;
  result = ScheduleUtils_CheckScenarioScheduled(this->hScheduleTable_, strScenarioName, &bAllScheduled);
  ERRIFGOTO(result, _EXIT);

  if (bAllScheduled == TRUE) {
    result = ScheduleUtils_IntializeScenario(this->hScheduleTable_, strScenarioName, this);
    ERRIFGOTO(result, _EXIT);

    result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_INITIALIZED);
    ERRIFGOTO(result, _EXIT);

    *pbScheduled = TRUE;
  } else {
    // SOPLOG_DEBUG("ScheduleUtils_CheckScenarioScheduled FAIL");

    *pbScheduled = FALSE;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnCancelScenario(cap_string strScenarioName) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnCancelScenario %s", CAPString_LowPtr(strScenarioName, NULL));

  // pass

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnGlobalUpdate(int i) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnGlobalUpdate");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnSuperScheduleRequest(SScheduleTask *pstScheduleTask, cap_bool *pbScheduled) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bSchedulable = FALSE;
  cap_handle hMappedThingNameList = NULL;
  SScheduleTask *pstNewScheduleTask = NULL;
  cap_handle hTempCandidateList = NULL;
  cap_handle hCandidateList = NULL;
  cap_string strTempThingName = NULL;
  cap_string strNewThingName = NULL;
  int nLen = 0;
  int nPeriodMs = -1;
  long long llExecTimeMs = -1;
  cap_bool bIsSuper = -1;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperScheduleRequest");

  result = CAPLinkedList_Create(&hMappedThingNameList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Create(&hTempCandidateList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Create(&hCandidateList);
  ERRIFGOTO(result, _EXIT);

  SOPLOG_DEBUG("hTagList:");

  if (pstScheduleTask->hTagList != NULL) {
    result = CAPLinkedList_GetLength(pstScheduleTask->hTagList, &nLen);
    ERRIFGOTO(result, _EXIT);
    if (nLen > 0) {
      result = CAPLinkedList_Traverse(pstScheduleTask->hTagList, PrintStringList, NULL);
      ERRIFGOTO(result, _EXIT);
    }
  }

  // CHECK status: Check schedulability of the requested service
  if (pstScheduleTask->enScheduleStatus == SCHEDULE_STATUS_CHECK) {
    // TODO: pstScheduleTask->strThingName is now SUPER
    // use only function name to find thing(s)
    result = DBHandler_GetCandidateList(pstScheduleTask->hTagList, pstScheduleTask->strFunctionName,
                                        SERVICE_TYPE_FUNCTION, hTempCandidateList);
    if (result == ERR_CAP_NOT_FOUND) {
      SOPLOG_DEBUG("Candidate Not Found: %s", CAPString_LowPtr(pstScheduleTask->strFunctionName, NULL));
      *pbScheduled = FALSE;
      result = ERR_CAP_NOERROR;
      goto _EXIT;
    }

    result = CAPLinkedList_GetLength(hTempCandidateList, &nLen);
    ERRIFGOTO(result, _EXIT);

    if (nLen == 0) {
      SOPLOG_DEBUG("Candidate Not Found: %s", CAPString_LowPtr(pstScheduleTask->strFunctionName, NULL));
      *pbScheduled = FALSE;
      result = ERR_CAP_NOERROR;
      goto _EXIT;
    }

    cap_bool bSchedulable = FALSE;
    for (int i = 0; i < nLen; i++) {
      result = CAPLinkedList_Get(hTempCandidateList, LINKED_LIST_OFFSET_FIRST, 0, (void **)&strTempThingName);
      ERRIFGOTO(result, _EXIT);

      result = ServiceTable_GetExecTime(this->hServiceTable_, strTempThingName, pstScheduleTask->strFunctionName,
                                        &llExecTimeMs);
      ERRIFGOTO(result, _EXIT);

      result =
          ServiceTable_GetIsSuper(this->hServiceTable_, strTempThingName, pstScheduleTask->strFunctionName, &bIsSuper);
      ERRIFGOTO(result, _EXIT);

      if (bIsSuper) {
        bSchedulable = TRUE;  // Assume Super Service is always available
      } else {
        SOPLOG_DEBUG("OnSuperScheduleRequest - CheckSchedulability %s", CAPString_LowPtr(strTempThingName, NULL));

        result = ScheduleUtils_CheckSchedulability(this->hScheduleTable_, this->hScenarioTable_, this->hServiceTable_,
                                                   strTempThingName, pstScheduleTask->strFunctionName, llExecTimeMs,
                                                   pstScheduleTask->nPeriodMs, &bSchedulable);
        ERRIFGOTO(result, _EXIT);
      }

      if (bSchedulable) {
        strNewThingName = CAPString_New();

        result = CAPString_Set(strNewThingName, strTempThingName);
        ERRIFGOTO(result, _EXIT);

        // SOPLOG_DEBUG("Add %s to hCandidateList", CAPString_LowPtr(strNewThingName, NULL));

        result = CAPLinkedList_Add(hCandidateList, LINKED_LIST_OFFSET_FIRST, 0, strNewThingName);
        ERRIFGOTO(result, _EXIT);
      } else {
        // SOPLOG_DEBUG("Exclude %s from hCandidateList", CAPString_LowPtr(strThingName, NULL));
      }

      *pbScheduled |= bSchedulable;
    }

    if (*pbScheduled == TRUE) {
      cap_string strThingNameCopied = CAPString_New();
      ERRMEMGOTO(strThingNameCopied, result, _EXIT);

      result = this->OnMapService(pstScheduleTask->strFunctionName, hCandidateList, &strThingNameCopied);
      ERRIFGOTO(result, _EXIT);

      result = CAPLinkedList_Add(hMappedThingNameList, LINKED_LIST_OFFSET_FIRST, 0, strThingNameCopied);
      ERRIFGOTO(result, _EXIT);

      // this will be freed on hMappedThingNameList destroy.
      strThingNameCopied = NULL;

      result = ScheduleTable_AddSuperThingRequest(this->hScheduleTable_, CAPSTR_SUPER_THING_REQUEST,
                                                  pstScheduleTask->strRequestKey, pstScheduleTask->strFunctionName,
                                                  hMappedThingNameList, SERVICE_TYPE_FUNCTION);
      ERRIFGOTO(result, _EXIT);
    }
  }
  // CONFIRM status: Add the request to hSuperThingRequestHash.
  else if (pstScheduleTask->enScheduleStatus == SCHEDULE_STATUS_CONFIRM) {
    result = ScheduleTask_Copy(pstScheduleTask, &pstNewScheduleTask);
    ERRIFGOTO(result, _EXIT);

    // TODO: update schedule info.
    // just keep the key as a whitelist
    result = CAPHash_AddKey(this->hSuperThingRequestHash_, pstScheduleTask->strRequestKey, pstNewScheduleTask);
    // duplicated case is accepted. (UPDATE)
    if (result == ERR_CAP_DUPLICATED) {
      result = ERR_CAP_NOERROR;
    }
    ERRIFGOTO(result, _EXIT);

    SOPLOG_DEBUG("[SchedulingPolicies] OnSuperScheduleRequest CAPHash_AddKey %s", pstScheduleTask->strRequestKey->pszStr);

    result = ScheduleTable_SetState(this->hScheduleTable_, CAPSTR_SUPER_THING_REQUEST, pstScheduleTask->strRequestKey,
                                    pstScheduleTask->strFunctionName, SCHEDULE_STATE_DONE);
    ERRIFGOTO(result, _EXIT);

    *pbScheduled = TRUE;
  } else {
    ERRASSIGNGOTO(result, ERR_CAP_NOT_SUPPORTED, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hMappedThingNameList != NULL) {
    CAPLinkedList_Traverse(hMappedThingNameList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hMappedThingNameList);
  }
  if (hTempCandidateList != NULL) {
    CAPLinkedList_Traverse(hTempCandidateList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hTempCandidateList);
  }
  if (hCandidateList != NULL) {
    CAPLinkedList_Traverse(hCandidateList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&hCandidateList);
  }
  return result;
}

cap_result MySchedulingPolicies::OnSuperCancelRequest(cap_string strRequestKey) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperCancelRequest %s", CAPString_LowPtr(strRequestKey, NULL));

  // pass

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnThingRegister(cap_string strThingName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bIsAlive = FALSE;

  SOPLOG_DEBUG("[SchedulingPolicies] OnThingRegister");

  result = DBHandler_GetThingAliveness(strThingName, &bIsAlive);
  if (result == ERR_CAP_NOT_FOUND) {
    result = ERR_CAP_NOT_FOUND;
  } else if (!bIsAlive) {
    result = ERR_CAP_INTERNAL_FAIL;
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnThingUnregister(cap_string strThingName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strScenarioName = NULL;
  cap_handle hAffectedScenarioList = NULL;
  cap_bool bScheduled = FALSE;
  int nLen = 0;

  SOPLOG_DEBUG("[SchedulingPolicies] OnThingUnregister");

  result = ScheduleUtils_GetAffectedScenarioOnUnreg(this, strThingName, &hAffectedScenarioList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(hAffectedScenarioList, &nLen);
  ERRIFGOTO(result, _EXIT);

  for (int i = 0; i < nLen; i++) {
    result = CAPLinkedList_Get(hAffectedScenarioList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strScenarioName);
    ERRIFGOTO(result, _EXIT);

    // result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_STUCKED);
    // ERRIFGOTO(result, _EXIT);

    result = ScheduleTable_CancelByScenario(this->hScheduleTable_, this->hScenarioTable_, this->hServiceTable_,
                                            strScenarioName);
    ERRIFGOTO(result, _EXIT);

    result = this->OnUpdateScenario(strScenarioName, &bScheduled);
    ERRIFGOTO(result, _EXIT);

    if (bScheduled) {
      // result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_INITIALIZED);
      // ERRIFGOTO(result, _EXIT);

      // run again
      result = ScenarioTable_ClearExecution(this->hScenarioTable_, strScenarioName);
      ERRIFGOTO(result, _EXIT);

      result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_RUNNING);
      ERRIFGOTO(result, _EXIT);
    } else {
      result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_STUCKED);
      ERRIFGOTO(result, _EXIT);
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hAffectedScenarioList != NULL) {
    CAPLinkedList_Traverse(hAffectedScenarioList, DestroyStringList, NULL);
    CAPLinkedList_Destroy(&(hAffectedScenarioList));
  }

  return result;
}

cap_result MySchedulingPolicies::OnMiddlewareRegister(cap_string strMiddlewareName) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnMiddlewareRegister");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnMiddlewareUnregister(cap_string strMiddlewareName) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnMiddlewareUnregister");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnServiceReady(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnServiceReady");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnServiceBusy(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnServiceBusy");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// merge execution
cap_result MySchedulingPolicies::OnServiceSuccess(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;
  SServiceInfo *pstServiceInfo = NULL;
  SScenarioInfo *pstScenarioInfo = NULL;
  SExecutionNode *pstExecutionNode = NULL;
  SExecutionStatement *pstExecStatement = NULL;
  cap_handle hVariableHash = NULL;
  cap_bool bDirection = NO_MOVE;
  cap_handle hScenarioList = NULL;
  int nLen = -1;
  cap_string strScenarioName = NULL;

  SOPLOG_DEBUG("[SchedulingPolicies] OnServiceSuccess %s / %s / %s",
               CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL),
               CAPString_LowPtr(pstExecutionResult->strThingName, NULL),
               CAPString_LowPtr(pstExecutionResult->strServiceName, NULL));

  result = ScenarioTable_Get(this->hScenarioTable_, pstExecutionResult->strScenarioName, &pstScenarioInfo);
  // Exception Case 1. Not from my local Scenario --> Toss to child
  if (result == ERR_CAP_NOT_FOUND) {
    SOPLOG_WARN("The result has unknown scenario name!, toss to the child...");

    ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
  }

  if (pstScenarioInfo->enState != SCENARIO_STATE_EXECUTING) {
    SOPLOG_WARN("Scheduler_HandleExecutionResult: invalid state %d. make it stucked...", pstScenarioInfo->enState);

    pstScenarioInfo->enState = SCENARIO_STATE_STUCKED;

    ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
  }

  result = ScenarioTable_Lock(this->hScenarioTable_);
  ERRIFGOTO(result, _EXIT);

  // 1. Check if the current statement is action statement
  result = AppScriptModeler_GetCurrent(pstScenarioInfo->hScenarioModel, &pstExecutionNode);
  ERRIFGOTO(result, _EXIT_LOCK);

  if (pstExecutionNode->enType != ACTION_STATEMENT) {
    SOPLOG_WARN("The target scenario is not in executing state!, skip this result...");
    ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT_LOCK);
  }

  pstExecStatement = (SExecutionStatement *)pstExecutionNode->pstStatementData;

  // Exception Case 2. From my local Scenario but, it is the result from a sub
  // service of a super service....
  if (CAPString_IsEqual(pstExecStatement->strSubIdentifier, pstExecutionResult->strServiceName) == FALSE) {
    SOPLOG_DEBUG(
        "it is the result from a sub service of a super service... skip "
        "assignment");
    ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT_LOCK);
  }

  // 2. Init
  result = AppScriptModeler_GetVariableHash(pstScenarioInfo->hScenarioModel, &hVariableHash);
  ERRIFGOTO(result, _EXIT_LOCK);

  // 3. Keep the result to a variable if the statement has an assignment.
  if (pstExecStatement->hOutputList != NULL) {
    result = ScheduleUtils_AssignExecutionResult(hVariableHash, pstExecStatement->hOutputList, pstExecutionResult);
    ERRIFGOTO(result, _EXIT_LOCK);
  }

  // 4. Set State of the Service, Scenario according to the result.
  if (pstExecutionResult->nErrorCode != ERR_CAP_NOERROR) {
    result = ServiceTable_SetState(this->hServiceTable_, pstExecutionResult->strThingName,
                                   pstExecutionResult->strServiceName, SERVICE_STATE_ERROR);
    ERRIFGOTO(result, _EXIT_LOCK);

    pstScenarioInfo->enState = SCENARIO_STATE_STUCKED;
    ERRIFGOTO(result, _EXIT_LOCK);

    bDirection = NO_MOVE;
  } else {
    result = ServiceTable_SetState(this->hServiceTable_, pstExecutionResult->strThingName,
                                   pstExecutionResult->strServiceName, SERVICE_STATE_READY);

    pstExecStatement->nWaitingResultNum--;

    if (pstExecStatement->nWaitingResultNum == 0) {
      pstScenarioInfo->enState = SCENARIO_STATE_RUNNING;

      bDirection = TRUE;
    }
  }

  SOPLOG_DEBUG(
      "[Scheduler] %s HandleExecutionResult] Direction: %d, "
      "pstExecStmt->nWaitingResultNum: %d",
      CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL), bDirection, pstExecStatement->nWaitingResultNum);

  // 5. Move the scenario.
  if (bDirection != NO_MOVE) {
    result = AppScriptModeler_MoveToNext(pstScenarioInfo->hScenarioModel, bDirection, &pstExecutionNode);
    ERRIFGOTO(result, _EXIT_LOCK);

    if (pstExecutionNode->enType == FINISH_STATEMENT) {
      pstScenarioInfo->enState = SCENARIO_STATE_COMPLETED;
      SOPLOG_DEBUG("[Scheduler] %s HandleExecutionResult] FINISH_STATEMENT",
                   CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL));
    }

    if (pstExecutionNode->enType == LOOP_STATEMENT) {
      // temp codce for simulation
      json_object *pJsonObject = json_object_new_object();
      cap_string strPayload = CAPString_New();
      json_object_object_add(pJsonObject, "scenario",
                             json_object_new_string(CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL)));

      result = CAPString_SetLow(strPayload, json_object_to_json_string(pJsonObject), CAPSTRING_MAX);
      ERRIFGOTO(result, _EXIT);

      result = MqttMessageHandler_Publish(this->hChildMQTTHandler_, CAPSTR_TO_SIMULATOR_FINISH,
                                          CAPString_LowPtr(strPayload, NULL), CAPString_Length(strPayload));
      ERRIFGOTO(result, _EXIT);

      SAFE_CAPSTRING_DELETE(strPayload);
      SAFEJSONFREE(pJsonObject);
    }
  }

  ScenarioTable_Unlock(this->hScenarioTable_);

  //////////
  result = ScheduleUtils_GetWaitingScenarioList(this->hWaitQueue_, pstExecutionResult->strThingName,
                                                pstExecutionResult->strServiceName, &hScenarioList);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(hScenarioList, &nLen);
  ERRIFGOTO(result, _EXIT);

  SOPLOG_DEBUG("Waiting Scenario: %d", nLen);

  for (int i = 0; i < nLen; i++) {
    result = CAPLinkedList_Get(hScenarioList, LINKED_LIST_OFFSET_FIRST, i, (void **)&strScenarioName);
    ERRIFGOTO(result, _EXIT);
    SOPLOG_DEBUG("Waiting Scenario Name: %s", CAPString_LowPtr(strScenarioName, NULL));

    result = ScenarioTable_Get(this->hScenarioTable_, strScenarioName, &pstScenarioInfo);
    // Exception Case 1. Not from my local Scenario --> Toss to child
    if (result == ERR_CAP_NOT_FOUND) {
      SOPLOG_WARN("The result has unknown scenario name!, toss to the child...");

      ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
    }

    SOPLOG_DEBUG("Waiting Scenario Name: %s", CAPString_LowPtr(strScenarioName, NULL));

    if (pstScenarioInfo->enState != SCENARIO_STATE_EXECUTING) {
      SOPLOG_WARN("Scheduler_HandleExecutionResult: invalid state %d. make it stucked...", pstScenarioInfo->enState);

      pstScenarioInfo->enState = SCENARIO_STATE_STUCKED;

      ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
    }

    result = ScenarioTable_Lock(this->hScenarioTable_);
    ERRIFGOTO(result, _EXIT);

    // 1. Check if the current statement is action statement
    result = AppScriptModeler_GetCurrent(pstScenarioInfo->hScenarioModel, &pstExecutionNode);
    ERRIFGOTO(result, _EXIT_LOCK);

    if (pstExecutionNode->enType != ACTION_STATEMENT) {
      SOPLOG_WARN("The target scenario is not in executing state!, skip this result...");
      ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT_LOCK);
    }

    pstExecStatement = (SExecutionStatement *)pstExecutionNode->pstStatementData;

    // Exception Case 2. From my local Scenario but, it is the result from a sub
    // service of a super service....
    if (CAPString_IsEqual(pstExecStatement->strSubIdentifier, pstExecutionResult->strServiceName) == FALSE) {
      SOPLOG_DEBUG(
          "it is the result from a sub service of a super service... skip "
          "assignment");
      ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT_LOCK);
    }

    // 2. Init
    result = AppScriptModeler_GetVariableHash(pstScenarioInfo->hScenarioModel, &hVariableHash);
    ERRIFGOTO(result, _EXIT_LOCK);

    // 3. Keep the result to a variable if the statement has an assignment.
    if (pstExecStatement->hOutputList != NULL) {
      result = ScheduleUtils_AssignExecutionResult(hVariableHash, pstExecStatement->hOutputList, pstExecutionResult);
      ERRIFGOTO(result, _EXIT_LOCK);
    }

    // 4. Set State of the Service, Scenario according to the result.
    if (pstExecutionResult->nErrorCode != ERR_CAP_NOERROR) {
      result = ServiceTable_SetState(this->hServiceTable_, pstExecutionResult->strThingName,
                                     pstExecutionResult->strServiceName, SERVICE_STATE_ERROR);
      ERRIFGOTO(result, _EXIT_LOCK);

      pstScenarioInfo->enState = SCENARIO_STATE_STUCKED;
      ERRIFGOTO(result, _EXIT_LOCK);

      bDirection = NO_MOVE;
    } else {
      result = ServiceTable_SetState(this->hServiceTable_, pstExecutionResult->strThingName,
                                     pstExecutionResult->strServiceName, SERVICE_STATE_READY);

      pstExecStatement->nWaitingResultNum--;

      if (pstExecStatement->nWaitingResultNum == 0) {
        pstScenarioInfo->enState = SCENARIO_STATE_RUNNING;

        bDirection = TRUE;
      }
    }

    SOPLOG_DEBUG(
        "[Scheduler] %s HandleExecutionResult] Direction: %d, "
        "pstExecStmt->nWaitingResultNum: %d",
        CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL), bDirection, pstExecStatement->nWaitingResultNum);

    // 5. Move the scenario.
    if (bDirection != NO_MOVE) {
      result = AppScriptModeler_MoveToNext(pstScenarioInfo->hScenarioModel, bDirection, &pstExecutionNode);
      ERRIFGOTO(result, _EXIT_LOCK);

      if (pstExecutionNode->enType == FINISH_STATEMENT) {
        pstScenarioInfo->enState = SCENARIO_STATE_COMPLETED;
        SOPLOG_DEBUG("[Scheduler] %s HandleExecutionResult] FINISH_STATEMENT",
                     CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL));
      }

      if (pstExecutionNode->enType == LOOP_STATEMENT) {
        // temp codce for simulation
        json_object *pJsonObject = json_object_new_object();
        cap_string strPayload = CAPString_New();
        json_object_object_add(pJsonObject, "scenario",
                               json_object_new_string(CAPString_LowPtr(pstExecutionResult->strScenarioName, NULL)));

        result = CAPString_SetLow(strPayload, json_object_to_json_string(pJsonObject), CAPSTRING_MAX);
        ERRIFGOTO(result, _EXIT);

        result = MqttMessageHandler_Publish(this->hChildMQTTHandler_, CAPSTR_TO_SIMULATOR_FINISH,
                                            CAPString_LowPtr(strPayload, NULL), CAPString_Length(strPayload));
        ERRIFGOTO(result, _EXIT);

        SAFE_CAPSTRING_DELETE(strPayload);
        SAFEJSONFREE(pJsonObject);
      }
    }

    ScenarioTable_Unlock(this->hScenarioTable_);
  }

  result = ERR_CAP_NOERROR;
_EXIT_LOCK:
  ScenarioTable_Unlock(this->hScenarioTable_);
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnServiceError(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bScheduled = FALSE;

  SOPLOG_DEBUG("[SchedulingPolicies] OnServiceError");

  result = ScenarioTable_SetState(this->hScenarioTable_, pstExecutionResult->strScenarioName, SCENARIO_STATE_STUCKED);
  ERRIFGOTO(result, _EXIT);

  result = ServiceTable_SetState(this->hServiceTable_, pstExecutionResult->strThingName,
                                 pstExecutionResult->strServiceName, SERVICE_STATE_ERROR);
  ERRIFGOTO(result, _EXIT);

  // remap
  result = ScheduleTable_CancelByScenario(this->hScheduleTable_, this->hScenarioTable_, this->hServiceTable_,
                                          pstExecutionResult->strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = this->OnUpdateScenario(pstExecutionResult->strScenarioName, &bScheduled);
  ERRIFGOTO(result, _EXIT);

  if (bScheduled) {
    // result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_INITIALIZED);
    // ERRIFGOTO(result, _EXIT);

    // run again
    result = ScenarioTable_ClearExecution(this->hScenarioTable_, pstExecutionResult->strScenarioName);
    ERRIFGOTO(result, _EXIT);

    result = ScenarioTable_SetState(this->hScenarioTable_, pstExecutionResult->strScenarioName, SCENARIO_STATE_RUNNING);
    ERRIFGOTO(result, _EXIT);
  } else {
    result = ScenarioTable_SetState(this->hScenarioTable_, pstExecutionResult->strScenarioName, SCENARIO_STATE_STUCKED);
    ERRIFGOTO(result, _EXIT);
  }
  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnServiceTimeout(cap_string strScenarioName, int nTry) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_bool bScheduled = FALSE;

  SOPLOG_DEBUG("[SchedulingPolicies] OnServiceTimeout");

  // result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_STUCKED);
  // ERRIFGOTO(result, _EXIT);

  result = ScheduleTable_CancelByScenario(this->hScheduleTable_, this->hScenarioTable_, this->hServiceTable_,
                                          strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = this->OnUpdateScenario(strScenarioName, &bScheduled);
  ERRIFGOTO(result, _EXIT);

  if (bScheduled) {
    // result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_INITIALIZED);
    // ERRIFGOTO(result, _EXIT);

    // run again
    result = ScenarioTable_ClearExecution(this->hScenarioTable_, strScenarioName);
    ERRIFGOTO(result, _EXIT);

    result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_RUNNING);
    ERRIFGOTO(result, _EXIT);
  } else {
    result = ScenarioTable_SetState(this->hScenarioTable_, strScenarioName, SCENARIO_STATE_STUCKED);
    ERRIFGOTO(result, _EXIT);
  }
  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnSuperServiceReady(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperServiceReady");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSuperServiceBusy(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperServiceBusy");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSuperServiceSuccess(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperServiceSuccess");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSuperServiceError(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperServiceError");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSuperServiceTimeout(cap_string strRequestKey, int nTry) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperServiceTimeout");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnSubServiceReady(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSubServiceReady");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSubServiceBusy(SRunTask *pstRunTask) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSubServiceBusy");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSubServiceSuccess(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSubServiceSuccess");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSubServiceError(SExecutionResult *pstExecutionResult) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSubServiceError");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}
cap_result MySchedulingPolicies::OnSubServiceTimeout(cap_string strRequestKey, int nTry) {
  cap_result result = ERR_CAP_UNKNOWN;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSubServiceTimeout");

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result MySchedulingPolicies::OnSuperScheduleResult(SScheduleResult *pstScheduleResult) {
  cap_result result = ERR_CAP_UNKNOWN;
  SScenarioInfo *pstScenarioInfo = NULL;
  cap_bool bAllScheduled = TRUE;
  cap_string strScenarioName = pstScheduleResult->strScenarioName;
  cap_handle hTargetScenarioTable = NULL;
  cap_handle hTargetScheduleTable = NULL;

  SOPLOG_DEBUG("[SchedulingPolicies] OnSuperScheduleResult");

  // FIXME: on update the scenario is already in Scenario Table.
  result = ScenarioTable_Get(this->hTempScenarioTable_, strScenarioName, &pstScenarioInfo);
  if (result == ERR_CAP_NOT_FOUND) {
    result = ScenarioTable_Get(this->hScenarioTable_, strScenarioName, &pstScenarioInfo);
    if (result == ERR_CAP_NOERROR) {
      hTargetScenarioTable = this->hScenarioTable_;
      hTargetScheduleTable = this->hScheduleTable_;
    } else {
      // ERRASSIGNGOTO(result, ERR_CAP_INVALID_ACCESS, _EXIT);
      // toss to child or parent
      ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
    }
  } else if (result == ERR_CAP_NOERROR) {
    hTargetScenarioTable = this->hTempScenarioTable_;
    hTargetScheduleTable = this->hTempScheduleTable_;
  }

  // if (pstScenarioInfo->enState != SCENARIO_STATE_SCHEDULING) {
  //   ERRASSIGNGOTO(result, ERR_CAP_INVALID_DATA, _EXIT);
  // } else
  if (pstScheduleResult->nErrorCode != ERR_CAP_NOERROR) {
    SOPLOG_DEBUG("Scenario %s - Super Schedule Error: %d", CAPString_LowPtr(strScenarioName, NULL),
                 pstScheduleResult->nErrorCode);
    result = ScenarioTable_SetState(hTargetScenarioTable, strScenarioName, SCENARIO_STATE_STUCKED);

    ERRASSIGNGOTO(result, ERR_CAP_NOERROR, _EXIT);
  }

  result = ScheduleUtils_ApplySuperScheduleResult(hTargetScheduleTable, strScenarioName, pstScheduleResult);
  ERRIFGOTO(result, _EXIT);

  // Check again if this scenario is fully scheduled.
  result = ScheduleUtils_CheckScenarioScheduled(hTargetScheduleTable, strScenarioName, &bAllScheduled);
  ERRIFGOTO(result, _EXIT);

  if (bAllScheduled == TRUE) {
    result = ScheduleUtils_IntializeScenario(hTargetScheduleTable, strScenarioName, this);
    ERRIFGOTO(result, _EXIT);

    if (hTargetScenarioTable == this->hScenarioTable_) {
      result = ScenarioTable_SetState(hTargetScenarioTable, strScenarioName, SCENARIO_STATE_INITIALIZED);
      ERRIFGOTO(result, _EXIT);
    } else if (hTargetScenarioTable == this->hTempScenarioTable_) {
      result = this->OnScheduleScenarioConfirm(strScenarioName);
      ERRIFGOTO(result, _EXIT);
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

MySchedulingPolicies::MySchedulingPolicies(void *middleware_name, void *service_table, void *scenario_table,
                                   void *schedule_table, void *tmp_scenario_table, void *tmp_schedule_table,
                                   void *super_thing_request_hash, void *run_queue, void *wait_queue, void *event_queue,
                                   void *schedule_queue, void *complete_queue, void *parent_mqtt_handler,
                                   void *child_mqtt_handler) {
  strMiddlewareName_ = (cap_string)middleware_name;
  hServiceTable_ = (cap_handle)service_table;
  hScenarioTable_ = (cap_handle)scenario_table;
  hScheduleTable_ = (cap_handle)schedule_table;
  hTempScenarioTable_ = (cap_handle)tmp_scenario_table;
  hTempScheduleTable_ = (cap_handle)tmp_schedule_table;
  hSuperThingRequestHash_ = (cap_handle)super_thing_request_hash;
  hRunQueue_ = (cap_handle)run_queue;
  hWaitQueue_ = (cap_handle)wait_queue;
  hEventQueue_ = (cap_handle)event_queue;
  hScheduleQueue_ = (cap_handle)schedule_queue;
  hCompleteQueue_ = (cap_handle)complete_queue;
  hParentMQTTHandler_ = (cap_handle)parent_mqtt_handler;
  hChildMQTTHandler_ = (cap_handle)child_mqtt_handler;
};

MySchedulingPolicies::~MySchedulingPolicies() {}