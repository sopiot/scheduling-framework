#include "sop_topic_utils.h"

#include "CAPLinkedList.h"
#include "mqtt_utils.h"

#define TOPIC_SEPATAOR '/'

CALLBACK cap_result DestroyTopicList(IN int nOffset, IN void *pData,
                                     IN void *pUserData) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strString = NULL;

  strString = pData;

  SAFE_CAPSTRING_DELETE(strString);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result TopicListToString(IN cap_handle hTopicItemList,
                             IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strItem = NULL;
  int nLinkedListSize = 0;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  result = CAPLinkedList_GetLength(hTopicItemList, &nLinkedListSize);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST, 0,
                             (void **)&strItem);
  ERRIFGOTO(result, _EXIT);

  result = CAPString_SetLow(strTopic, CAPString_LowPtr(strItem, NULL),
                            CAPSTRING_MAX);
  ERRIFGOTO(result, _EXIT);

  for (int i = 1; i < nLinkedListSize; i++) {
    result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST, i,
                               (void **)&strItem);
    ERRIFGOTO(result, _EXIT);

    result = CAPString_AppendLow(strTopic, "/", 1);
    ERRIFGOTO(result, _EXIT);

    result = CAPString_AppendLow(strTopic, CAPString_LowPtr(strItem, NULL),
                                 CAPSTRING_MAX);
    ERRIFGOTO(result, _EXIT);
  }

  SOPLOG_DEBUG("TopicListToString: %s", CAPString_LowPtr(strTopic, NULL));

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result TopicStringToList(IN cap_string strTopic,
                             IN OUT cap_handle hTopicItemList) {
  cap_result result = ERR_CAP_UNKNOWN;
  int nLinkedListSize = 0;
  int nLinkedListIndex = 0;
  cap_string strTemp = NULL;
  cap_string strToken = NULL;
  int nTopicStrIndex = 0;
  int nSeparatorIndex = 0;

  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  result = CAPLinkedList_GetLength(hTopicItemList, &nLinkedListSize);
  ERRIFGOTO(result, _EXIT);

  while (nSeparatorIndex != CAPSTR_INDEX_NOT_FOUND) {
    strToken = CAPString_New();
    ERRMEMGOTO(strToken, result, _EXIT);

    nSeparatorIndex =
        CAPString_FindChar(strTopic, nTopicStrIndex, TOPIC_SEPATAOR);
    if (nSeparatorIndex == CAPSTR_INDEX_NOT_FOUND) {
      // TOPIC_SEPATAOR not found
      result =
          CAPString_SetSub(strToken, strTopic, nTopicStrIndex, CAPSTRING_MAX);
      ERRIFGOTO(result, _EXIT);
    } else {
      result = CAPString_SetSub(strToken, strTopic, nTopicStrIndex,
                                nSeparatorIndex - nTopicStrIndex);
      ERRIFGOTO(result, _EXIT);
    }

    if (nLinkedListIndex < nLinkedListSize) {
      // delete an existing data to reuse the node
      result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                                 nLinkedListIndex, (void **)&strTemp);
      ERRIFGOTO(result, _EXIT);

      SAFE_CAPSTRING_DELETE(strTemp);

      result = CAPLinkedList_Set(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                                 nLinkedListIndex, strToken);
      ERRIFGOTO(result, _EXIT);
    } else {
      result = CAPLinkedList_Add(hTopicItemList, LINKED_LIST_OFFSET_LAST, 0,
                                 strToken);
      ERRIFGOTO(result, _EXIT);

      // update nLinkedListSize
      result = CAPLinkedList_GetLength(hTopicItemList, &nLinkedListSize);
      ERRIFGOTO(result, _EXIT);
    }
    nLinkedListIndex++;

    // set NULL to not free inserted strToken
    strToken = NULL;

    // points the index next to TOPIC_SEPARATOR
    if (nSeparatorIndex != CAPSTR_INDEX_NOT_FOUND) {
      nTopicStrIndex = nSeparatorIndex + 1;
    }
  }

  // remove the remaining nodes
  if (nLinkedListIndex < nLinkedListSize) {
    // use the nLinkedListIndex as a loop variable
    for (; nLinkedListIndex < nLinkedListSize; nLinkedListIndex++) {
      result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_LAST, -1,
                                 (void **)&strTemp);
      ERRIFGOTO(result, _EXIT);

      SAFE_CAPSTRING_DELETE(strTemp);

      result =
          CAPLinkedList_Remove(hTopicItemList, LINKED_LIST_OFFSET_LAST, -1);
      ERRIFGOTO(result, _EXIT);
    }
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strToken);
  return result;
}

cap_result GetProtocolFromTopic(IN cap_handle hTopicItemList,
                                OUT cap_string *pstrProtocol) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  // SoPIoT topic message has a protocol at the first item
  result =
      GetItemFromTopicList_Str(hTopicItemList, TOPIC_LEVEL_FIRST, pstrProtocol);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GetProtocolFromTopicString(IN cap_string strTopic,
                                      OUT cap_string *pstrProtocol) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hTopicItemList = NULL;
  cap_string strTemp = NULL;
  cap_string strProtocol = NULL;

  strProtocol = CAPString_New();
  ERRMEMGOTO(strProtocol, result, _EXIT);

  result = CAPLinkedList_Create(&hTopicItemList);
  ERRMEMGOTO(hTopicItemList, result, _EXIT);

  result = TopicStringToList(strTopic, hTopicItemList);
  ERRIFGOTO(result, _EXIT);

  result = GetProtocolFromTopic(hTopicItemList, &strTemp);
  ERRIFGOTO(result, _EXIT);

  result = CAPString_Set(strProtocol, strTemp);
  ERRIFGOTO(result, _EXIT);

  *pstrProtocol = strProtocol;

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hTopicItemList != NULL) {
    CAPLinkedList_Traverse(hTopicItemList, DestroyTopicList, NULL);
    CAPLinkedList_Destroy(&hTopicItemList);
  }
  return result;
}

cap_result GetCategoryFromTopic(IN cap_handle hTopicItemList,
                                OUT cap_string *pstrCategory) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  // SoPIoT topic message has a category at the second item
  result = GetItemFromTopicList_Str(hTopicItemList, TOPIC_LEVEL_SECOND,
                                    pstrCategory);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GetSubCategoryFromTopic(IN cap_handle hTopicItemList,
                                   OUT cap_string *pstrSubCategory) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  // SoPIoT topic message has a sub category at the third item
  result = GetItemFromTopicList_Str(hTopicItemList, TOPIC_LEVEL_THIRD,
                                    pstrSubCategory);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GetClientIdFromEMTopic(IN cap_handle hTopicItemList,
                                  OUT cap_string *pstrClientId) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strProtocol = NULL;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);

  // check if the topic is EM topic
  result =
      GetItemFromTopicList_Str(hTopicItemList, TOPIC_LEVEL_FIRST, &strProtocol);
  ERRIFGOTO(result, _EXIT);

  if (CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_EM) != TRUE) {
    SOPLOG_WARN("The topic is not EM topic %s",
                CAPString_LowPtr(strProtocol, NULL));
    ERRASSIGNGOTO(result, ERR_CAP_INVALID_PARAM, _EXIT);
  }

  // EM topic message has clientId at the last item
  result = GetLastItemFromTopicList_Str(hTopicItemList, pstrClientId);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// Schedule Request Topic:
// TM/SCHEDULE/[FunctionName]/[ThingName]/[MiddlewareName]/[RequesterName]
cap_result ParseScheduleRequestTopic(IN cap_handle hTopicItemList,
                                     OUT cap_string *pstrFunctionName,
                                     OUT cap_string *pstrThingName,
                                     OUT cap_string *pstrTargetMiddlewareName,
                                     OUT cap_string *pstrRequesterName) {
  cap_result result = ERR_CAP_UNKNOWN;

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_THIRD, (void **)pstrFunctionName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_FOURTH, (void **)pstrThingName);
  ERRIFGOTO(result, _EXIT);

  result =
      CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                        TOPIC_LEVEL_FIFTH, (void **)pstrTargetMiddlewareName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_SIXTH, (void **)pstrRequesterName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// Execution Request Topic:
// TM/EXECUTE/[FunctionName]/[ThingName]/[MiddlewareName]/[RequesterName]
cap_result ParseExecutionRequestTopic(IN cap_handle hTopicItemList,
                                      OUT cap_string *pstrFunctionName,
                                      OUT cap_string *pstrThingName,
                                      OUT cap_string *pstrTargetMiddlewareName,
                                      OUT cap_string *pstrRequesterName) {
  cap_result result = ERR_CAP_UNKNOWN;

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_THIRD, (void **)pstrFunctionName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_FOURTH, (void **)pstrThingName);
  ERRIFGOTO(result, _EXIT);

  if (pstrTargetMiddlewareName != NULL) {
    result =
        CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                          TOPIC_LEVEL_FIFTH, (void **)pstrTargetMiddlewareName);
    ERRIFGOTO(result, _EXIT);
  }

  if (pstrRequesterName != NULL) {
    result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                               TOPIC_LEVEL_SIXTH, (void **)pstrRequesterName);
    ERRIFGOTO(result, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result ParseExecutionRequestTopicString(
    IN cap_string strTopic, IN OUT cap_string strFunctionName,
    IN OUT cap_string strThingName, IN OUT cap_string strTargetMiddlewareName,
    IN OUT cap_string strRequesterName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hTopicItemList = NULL;
  cap_string strTempFunctionName = NULL;
  cap_string strTempThingName = NULL;
  cap_string strTempTargetMiddlewareName = NULL;
  cap_string strTempRequesterName = NULL;

  result = CAPLinkedList_Create(&hTopicItemList);
  ERRMEMGOTO(hTopicItemList, result, _EXIT);

  result = TopicStringToList(strTopic, hTopicItemList);
  ERRIFGOTO(result, _EXIT);

  if (strTargetMiddlewareName == NULL && strRequesterName == NULL) {
    result = ParseExecutionRequestTopic(hTopicItemList, &strTempFunctionName,
                                        &strTempThingName, NULL, NULL);
    ERRIFGOTO(result, _EXIT);
  } else {
    result = ParseExecutionRequestTopic(
        hTopicItemList, &strTempFunctionName, &strTempThingName,
        &strTempTargetMiddlewareName, &strTempRequesterName);
    ERRIFGOTO(result, _EXIT);

    result =
        CAPString_Set(strTargetMiddlewareName, strTempTargetMiddlewareName);
    ERRIFGOTO(result, _EXIT);

    result = CAPString_Set(strRequesterName, strTempRequesterName);
    ERRIFGOTO(result, _EXIT);
  }

  result = CAPString_Set(strFunctionName, strTempFunctionName);
  ERRIFGOTO(result, _EXIT);

  result = CAPString_Set(strThingName, strTempThingName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hTopicItemList != NULL) {
    CAPLinkedList_Traverse(hTopicItemList, DestroyTopicList, NULL);
    CAPLinkedList_Destroy(&hTopicItemList);
  }
  return result;
}

// TM/RESULT/{EXECUTE,SCHEDULE}/[FunctionName]/[ThingName]
// {SM/PC}/RESULT/{EXECUTE,SCHEDULE}/[SuperFunctionName]/[SuperThingName]/[MiddlewareName]/[RequesterMWName]
cap_result ParseRequestResultTopic(IN cap_handle hTopicItemList,
                                   OUT cap_string *pstrFunctionName,
                                   OUT cap_string *pstrThingName,
                                   OUT cap_string *pstrTargetMiddlewareName,
                                   OUT cap_string *pstrRequesterName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strProtocol = NULL;
  int nLen = 0;

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_FOURTH, (void **)pstrFunctionName);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                             TOPIC_LEVEL_FIFTH, (void **)pstrThingName);
  ERRIFGOTO(result, _EXIT);

  result = GetProtocolFromTopic(hTopicItemList, &strProtocol);
  ERRIFGOTO(result, _EXIT);

  result = CAPLinkedList_GetLength(hTopicItemList, &nLen);
  ERRIFGOTO(result, _EXIT);

  if (nLen > 5 && (CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_TM) ||
                   CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_SM) ||
                   CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_MS) ||
                   CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_PC) ||
                   CAPString_IsEqual(strProtocol, CAPSTR_PROTOCOL_CP))) {
    result =
        CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                          TOPIC_LEVEL_SIXTH, (void **)pstrTargetMiddlewareName);
    if (result == ERR_CAP_NOT_FOUND) {
      *pstrTargetMiddlewareName = NULL;
      result = ERR_CAP_NOERROR;
    }
    ERRIFGOTO(result, _EXIT);

    result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST,
                               TOPIC_LEVEL_SEVENTH, (void **)pstrRequesterName);
    if (result == ERR_CAP_NOT_FOUND) {
      *pstrRequesterName = NULL;
      result = ERR_CAP_NOERROR;
    }
    ERRIFGOTO(result, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result ParseRequestResultTopicString(
    IN cap_string strTopic, IN OUT cap_string strFunctionName,
    IN OUT cap_string strThingName, IN OUT cap_string strTargetMiddlewareName,
    IN OUT cap_string strRequesterName) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_handle hTopicItemList = NULL;
  cap_string strTempFunctionName = NULL;
  cap_string strTempThingName = NULL;
  cap_string strTempTargetMiddlewareName = NULL;
  cap_string strTempRequesterName = NULL;
  cap_string strProtocol = NULL;

  result = CAPLinkedList_Create(&hTopicItemList);
  ERRMEMGOTO(hTopicItemList, result, _EXIT);

  result = TopicStringToList(strTopic, hTopicItemList);
  ERRIFGOTO(result, _EXIT);

  result = ParseRequestResultTopic(
      hTopicItemList, &strTempFunctionName, &strTempThingName,
      &strTempTargetMiddlewareName, &strTempRequesterName);
  ERRIFGOTO(result, _EXIT);

  if (strTempTargetMiddlewareName == NULL) {
    strTargetMiddlewareName = NULL;
  } else if (strTargetMiddlewareName != NULL) {
    result =
        CAPString_Set(strTargetMiddlewareName, strTempTargetMiddlewareName);
    ERRIFGOTO(result, _EXIT);
  }

  if (strTempRequesterName == NULL) {
    strRequesterName = NULL;
  } else if (strRequesterName != NULL) {
    result = CAPString_Set(strRequesterName, strTempRequesterName);
    ERRIFGOTO(result, _EXIT);
  }

  result = CAPString_Set(strFunctionName, strTempFunctionName);
  ERRIFGOTO(result, _EXIT);

  result = CAPString_Set(strThingName, strTempThingName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  if (hTopicItemList != NULL) {
    CAPLinkedList_Traverse(hTopicItemList, DestroyTopicList, NULL);
    CAPLinkedList_Destroy(&hTopicItemList);
  }
  return result;
}

cap_result GenerateVerifyScenarioResultTopic(IN cap_string strRequesterName,
                                             IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/VERIFY_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateAddScenarioResultTopic(IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/ADD_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateDeleteScenarioResultTopic(IN cap_string strRequesterName,
                                             IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/DELETE_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateRunScenarioResultTopic(IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/RUN_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateStopScenarioResultTopic(IN cap_string strRequesterName,
                                           IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/STOP_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateScheduleScenarioResultTopic(IN cap_string strRequesterName,
                                               IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/SCHEDULE_SCENARIO/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateRegisterResultTopic(IN cap_string strRequesterName,
                                       IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "MT/RESULT/REGISTER/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateUnregisterResultTopic(IN cap_string strRequesterName,
                                         IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "MT/RESULT/UNREGISTER/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateAddTagResultTopic(IN cap_string strRequesterName,
                                     IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/ADD_TAG/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateDeleteTagResultTopic(IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/DELETE_TAG/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateSetAccessResultTopic(IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "ME/RESULT/SET_ACCESS/%s",
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// Value Publish Topic: [ThingName]/[ValueName]
cap_result GenerateValuePublishTopic(IN cap_string strThingName,
                                     IN cap_string strValueName,
                                     IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strThingName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strValueName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "%s/%s",
                                 CAPString_LowPtr(strThingName, NULL),
                                 CAPString_LowPtr(strValueName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateExecutionRequestTopic(IN cap_string strProtocol,
                                         IN cap_string strFunctionName,
                                         IN cap_string strThingName,
                                         IN cap_string strMiddlewareName,
                                         IN cap_string strRequesterName,
                                         IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strFunctionName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strThingName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  if (strMiddlewareName == NULL && strRequesterName == NULL) {
    // middleware and requester info is not required when requesting locally
    result = CAPString_PrintFormat(strTopic, "%s/EXECUTE/%s/%s",
                                   CAPString_LowPtr(strProtocol, NULL),
                                   CAPString_LowPtr(strFunctionName, NULL),
                                   CAPString_LowPtr(strThingName, NULL));
  } else if (strMiddlewareName != NULL && strRequesterName != NULL) {
    // requesting between middlewares
    result = CAPString_PrintFormat(strTopic, "%s/EXECUTE/%s/%s/%s/%s",
                                   CAPString_LowPtr(strProtocol, NULL),
                                   CAPString_LowPtr(strFunctionName, NULL),
                                   CAPString_LowPtr(strThingName, NULL),
                                   CAPString_LowPtr(strMiddlewareName, NULL),
                                   CAPString_LowPtr(strRequesterName, NULL));
  }
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

// Execution Result Topic: TM/RESULT/EXECUTE/[FunctionName]/[ThingName]
cap_result GenerateExecutionResultTopic(IN cap_string strProtocol,
                                        IN cap_string strFunctionName,
                                        IN cap_string strThingName,
                                        IN cap_string strMiddlewareName,
                                        IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strFunctionName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strThingName, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  if (strMiddlewareName == NULL && strRequesterName == NULL) {
    // middleware and requester info is not required when requesting locally
    result = CAPString_PrintFormat(strTopic, "%s/RESULT/EXECUTE/%s/%s",
                                   CAPString_LowPtr(strProtocol, NULL),
                                   CAPString_LowPtr(strFunctionName, NULL),
                                   CAPString_LowPtr(strThingName, NULL));
  } else if (strMiddlewareName != NULL && strRequesterName != NULL) {
    // requesting between middlewares
    result = CAPString_PrintFormat(strTopic, "%s/RESULT/EXECUTE/%s/%s/%s/%s",
                                   CAPString_LowPtr(strProtocol, NULL),
                                   CAPString_LowPtr(strFunctionName, NULL),
                                   CAPString_LowPtr(strThingName, NULL),
                                   CAPString_LowPtr(strMiddlewareName, NULL),
                                   CAPString_LowPtr(strRequesterName, NULL));
  }
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateServiceListTopic(IN EDestination eDst,
                                    IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  if (eDst == DST_PARENT) {
    result = CAPString_PrintFormat(strTopic, "CP/SERVICE_LIST/");
  } else if (eDst == DST_CHILD) {
    result = CAPString_PrintFormat(strTopic, "PC/SERVICE_LIST/");
  } else {
    ERRASSIGNGOTO(result, ERR_CAP_NOT_SUPPORTED, _EXIT);
  }
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateServiceListResultTopic(IN cap_string strProtocol,
                                          IN cap_string strRequesterName,
                                          IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strProtocol, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  // unicast
  if (strRequesterName != NULL) {
    result = CAPString_PrintFormat(strTopic, "%s/RESULT/SERVICE_LIST/%s",
                                   CAPString_LowPtr(strProtocol, NULL),
                                   CAPString_LowPtr(strRequesterName, NULL));
    ERRIFGOTO(result, _EXIT);
  }
  // broadcast
  else {
    result = CAPString_PrintFormat(strTopic, "%s/RESULT/SERVICE_LIST/",
                                   CAPString_LowPtr(strProtocol, NULL));
    ERRIFGOTO(result, _EXIT);
  }

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateScenarioListResultTopic(IN cap_string strProtocol,
                                           IN cap_string strRequesterName,
                                           IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strProtocol, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(strTopic, "%s/RESULT/SCENARIO_LIST/%s",
                                 CAPString_LowPtr(strProtocol, NULL),
                                 CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateScheduleRequestTopic(IN cap_string strProtocol,
                                        IN cap_string strTargetServiceName,
                                        IN cap_string strTargetThingName,
                                        IN cap_string strTargetMiddlewareName,
                                        IN cap_string strRequesterName,
                                        IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strProtocol, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTargetServiceName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTargetThingName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTargetMiddlewareName, NULL, result,
                     ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPString_PrintFormat(
      strTopic, "%s/SCHEDULE/%s/%s/%s/%s", CAPString_LowPtr(strProtocol, NULL),
      CAPString_LowPtr(strTargetServiceName, NULL),
      CAPString_LowPtr(strTargetThingName, NULL),
      CAPString_LowPtr(strTargetMiddlewareName, NULL),
      CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GenerateScheduleResultTopic(IN cap_string strProtocol,
                                       IN cap_string strTargetServiceName,
                                       IN cap_string strTargetThingName,
                                       IN cap_string strTargetMiddlewareName,
                                       IN cap_string strRequesterName,
                                       IN OUT cap_string strTopic) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strProtocol, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTargetMiddlewareName, NULL, result,
                     ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(strTargetThingName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTargetServiceName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strRequesterName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strTopic, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result =
      CAPString_PrintFormat(strTopic, "%s/RESULT/SCHEDULE/%s/%s/%s/%s",
                            CAPString_LowPtr(strProtocol, NULL),
                            CAPString_LowPtr(strTargetServiceName, NULL),
                            CAPString_LowPtr(strTargetThingName, NULL),
                            CAPString_LowPtr(strTargetMiddlewareName, NULL),
                            CAPString_LowPtr(strRequesterName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}