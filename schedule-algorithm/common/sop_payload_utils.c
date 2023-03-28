#include "sop_payload_utils.h"

#include "CAPLinkedList.h"
#include "jsonc_utils.h"

cap_result ParseSubScheduleRequestPayload(IN char *pszPayload,
                                          IN int nPayloadLen,
                                          OUT cap_string *pstrScenarioName,
                                          IN OUT EScheduleStatusType *penStatus,
                                          IN OUT int *pnPeriodMs,
                                          OUT cap_handle *phTagList) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonObject = NULL;
  json_object *pJsonTagList = NULL;
  cap_string strScheduleStatus = NULL;
  cap_string strScenarioName = NULL;
  cap_handle hTagList = NULL;

  IFVARERRASSIGNGOTO(pszPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_Create(&hTagList);
  ERRIFGOTO(result, _EXIT);

  strScenarioName = CAPString_New();
  ERRMEMGOTO(strScenarioName, result, _EXIT);

  strScheduleStatus = CAPString_New();
  ERRMEMGOTO(strScheduleStatus, result, _EXIT);

  result = Jsonc_Parse(&pJsonObject, pszPayload, nPayloadLen);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetString(pJsonObject, "scenario", strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetString(pJsonObject, "status", strScheduleStatus);
  ERRIFGOTO(result, _EXIT);

  if (CAPString_IsEqual(strScheduleStatus, CAPSTR_STATUS_CHECK) == TRUE) {
    *penStatus = SCHEDULE_STATUS_CHECK;
  } else if (CAPString_IsEqual(strScheduleStatus, CAPSTR_STATUS_CONFIRM) ==
             TRUE) {
    *penStatus = SCHEDULE_STATUS_CONFIRM;
  } else {
    *penStatus = -1;
    ERRASSIGNGOTO(result, ERR_CAP_NOT_SUPPORTED, _EXIT);
  }

  result = Jsonc_GetInt(pJsonObject, "period", pnPeriodMs);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetObjectOptional(pJsonObject, "tag_list", &pJsonTagList);
  ERRIFGOTO(result, _EXIT);

  cap_string strTagName = NULL;
  for (int i = 0; i < json_object_array_length(pJsonTagList); i++) {
    json_object *pJsonTag = json_object_array_get_idx(pJsonTagList, i);

    strTagName = CAPString_New();
    ERRMEMGOTO(strTagName, result, _EXIT);

    result = Jsonc_GetString(pJsonTag, "name", strTagName);
    ERRIFGOTO(result, _EXIT);

    result =
        CAPLinkedList_Add(hTagList, LINKED_LIST_OFFSET_LAST, 0, strTagName);
    ERRIFGOTO(result, _EXIT);

    strTagName = NULL;
  }

  *pstrScenarioName = strScenarioName;
  *phTagList = hTagList;

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strScheduleStatus);
  SAFEJSONFREE(pJsonObject);

  return result;
}

cap_result ParseScheduleRequestPayload(IN char *pszPayload, IN int nPayloadLen,
                                       OUT cap_string *pstrScenarioName,
                                       IN OUT EScheduleStatusType *penStatus,
                                       IN OUT int *pnPeriodMs) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonObject = NULL;
  cap_string strScheduleStatus = NULL;
  cap_string strScenarioName = NULL;

  IFVARERRASSIGNGOTO(pszPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  strScenarioName = CAPString_New();
  ERRMEMGOTO(strScenarioName, result, _EXIT);

  strScheduleStatus = CAPString_New();
  ERRMEMGOTO(strScheduleStatus, result, _EXIT);

  result = Jsonc_Parse(&pJsonObject, pszPayload, nPayloadLen);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetString(pJsonObject, "scenario", strScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetString(pJsonObject, "status", strScheduleStatus);
  ERRIFGOTO(result, _EXIT);

  if (CAPString_IsEqual(strScheduleStatus, CAPSTR_STATUS_CHECK) == TRUE) {
    *penStatus = SCHEDULE_STATUS_CHECK;
  } else if (CAPString_IsEqual(strScheduleStatus, CAPSTR_STATUS_CONFIRM) ==
             TRUE) {
    *penStatus = SCHEDULE_STATUS_CONFIRM;
  } else {
    *penStatus = -1;
    ERRASSIGNGOTO(result, ERR_CAP_NOT_SUPPORTED, _EXIT);
  }

  result = Jsonc_GetInt(pJsonObject, "period", pnPeriodMs);
  ERRIFGOTO(result, _EXIT);

  *pstrScenarioName = strScenarioName;

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFE_CAPSTRING_DELETE(strScheduleStatus);
  SAFEJSONFREE(pJsonObject);

  return result;
}

cap_result ParseScheduleRequestPayloadString(
    IN cap_string strPayload, OUT cap_string *pstrScenarioName,
    IN OUT EScheduleStatusType *penStatus, OUT int *pnPeriodMs) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonObject = NULL;

  IFVARERRASSIGNGOTO(strPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = ParseScheduleRequestPayload(CAPString_LowPtr(strPayload, NULL),
                                       CAPString_Length(strPayload),
                                       pstrScenarioName, penStatus, pnPeriodMs);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFEJSONFREE(pJsonObject);

  return result;
}

cap_result ParseExecutionRequestPayload(IN char *pszPayload, IN int nPayloadLen,
                                        OUT cap_string *pstrScenarioName) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonObject = NULL;
  cap_string strScenarioName = NULL;

  IFVARERRASSIGNGOTO(pszPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  strScenarioName = CAPString_New();
  ERRMEMGOTO(strScenarioName, result, _EXIT);

  result = Jsonc_Parse(&pJsonObject, pszPayload, nPayloadLen);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_GetString(pJsonObject, "scenario", strScenarioName);
  ERRIFGOTO(result, _EXIT);

  *pstrScenarioName = strScenarioName;

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFEJSONFREE(pJsonObject);

  return result;
}

// TODO: maybe... better if change to 'getter' way?
cap_result ParseExecutionRequestPayloadString(
    IN cap_string strPayload, OUT cap_string *pstrScenarioName) {
  cap_result result = ERR_CAP_UNKNOWN;

  IFVARERRASSIGNGOTO(strPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = ParseExecutionRequestPayload(CAPString_LowPtr(strPayload, NULL),
                                        CAPString_Length(strPayload),
                                        pstrScenarioName);
  ERRIFGOTO(result, _EXIT);

  result = ERR_CAP_NOERROR;
_EXIT:

  return result;
}

cap_result GenerateScheduleRequestPayload(IN cap_string strScenarioName,
                                          IN int nPeriodMs,
                                          IN OUT cap_string strPayload) {
  cap_result result = ERR_CAP_UNKNOWN;
  json_object *pJsonObject = NULL;

  IFVARERRASSIGNGOTO(strScenarioName, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(strPayload, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  pJsonObject = json_object_new_object();

  result = Jsonc_AddString(pJsonObject, "scenario",
                           CAPString_LowPtr(strScenarioName, NULL));
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_AddInt(pJsonObject, "period", nPeriodMs);
  ERRIFGOTO(result, _EXIT);

  result = Jsonc_ToString(pJsonObject, strPayload);
  ERRIFGOTO(result, _EXIT);

  SOPLOG_DEBUG("[GenerateScheduleRequestPayload] payload: %s",
               CAPString_LowPtr(strPayload, NULL));

  result = ERR_CAP_NOERROR;
_EXIT:
  SAFEJSONFREE(pJsonObject);

  return result;
}