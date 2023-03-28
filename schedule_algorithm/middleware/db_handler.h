#ifndef DBHANDLER_H_
#define DBHANDLER_H_

#include "AppScriptModeler.h"
#include "CAPString.h"
#include "hierarchy_manager.h"
#include "jsonc_utils.h"
#include "service_table.h"
#include "sop_common.h"
#include "thing_info_handler.h"
#include "thing_manager.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef cap_result (*CbFnTraverseScenario)(int nId, cap_string strScenarioName, cap_string strScenarioText,
                                           void *pUserData);

//----------------------------------------
// general functions
//----------------------------------------

cap_result DBHandler_OpenDB(IN char *pszMainDBFileName, IN char *pszValueLogDBFileName);
cap_result DBHandler_CloseDB();
cap_result DBHandler_GetDBTime(OUT char **ppszTimeStr);

//----------------------------------------
// packet generating functions
//----------------------------------------

cap_result DBHandler_GenerateServiceListJsonObject(IN EDestination eDst, IN OUT json_object **ppJsonObject);
cap_result DBHandler_GenerateScenarioListPayload(IN cap_handle hScheduler, IN OUT cap_string strPayload);
cap_result DBHandler_GenerateSensorValueMessage(IN char *pszThingName, IN char *pszValueName, IN char *pszPayload,
                                                OUT char **ppszMessage);

//----------------------------------------
// scenario related query
//----------------------------------------

cap_result DBHandler_AddScenario(cap_string strScenarioName, cap_string strScenarioText, int nPriority);
cap_result DBHandler_ClearScenarioDB();
cap_result DBHandler_DeleteScenario(IN int nScenarioId);
cap_result DBHandler_GetScenarioNameById(IN int nScenarioId, IN OUT cap_string strScenarioName);
cap_result DBHandler_GetScenarioIdByName(IN cap_string strScenarioName, IN OUT int *pnScenarioId);

//----------------------------------------
// thing related query
//----------------------------------------

cap_result DBHandler_ClearThingDB();
cap_result DBHandler_AddThing(IN SThingInfo *pstThing, IN cap_string strMiddlewareName);
cap_result DBHandler_DeleteThing(cap_string strThingName, int nMiddlewareName);
cap_result DBHandler_GetThingAliveness(IN cap_string strThingName, OUT cap_bool *pbIsAlive);
cap_result DBHandler_SetThingAliveness(IN cap_string strThingName, cap_bool bIsAlive);
cap_result DBHandler_UpdateThingLatestTime(IN char *pszThingName);
cap_result DBHandler_GenerateLocalThingAliveInfoArray(IN OUT SThingAliveInfo **ppstThingAliveInfoArray,
                                                      IN int *pnArrayLength);
cap_result DBHandler_GetOneThingNameByTagListAndServiceName(IN cap_handle hTageList, IN cap_string strServiceName,
                                                            IN EServiceType enServiceType, OUT cap_string strThingName);
cap_result DBHandler_GetCandidateList(IN cap_handle hTagList, IN cap_string strServiceName,
                                      IN EServiceType enServiceType, OUT cap_handle hMappedThingNameList);
cap_result DBHandler_GetThingNameListByScheduleKey(IN cap_string strScheduleKey, IN EServiceType enServiceType,
                                                   IN OUT cap_handle hCandidateList);

//----------------------------------------
// service related
//----------------------------------------

// general
cap_result DBHandler_SetServiceAvailability(cap_string strSuperThingName, cap_string strFunctionName,
                                            cap_bool bIsAvailable);
cap_result DBHandler_SetServiceAccess(cap_string strThingName, cap_string strFunctionName, cap_bool bIsPrivate);

// function
cap_result DBHandler_GetFunction(cap_string strThingName, cap_string strFunctionName, SFunctionInfo **ppstFunctionInfo);
cap_result DBHandler_GetArgument(IN cap_string strThingName, IN cap_string strFunctionName, IN int nOrder,
                                 OUT SArgument **ppstArgument);
cap_result DBHandler_GetNumberOfArgument(IN cap_string strThingName, IN cap_string strFunctionName,
                                         OUT int *pnNumberOfArgument);

// value
cap_result DBHandler_UpdateValue(IN char *pszThingName, IN char *pszValueName, IN char *pszPayload);
cap_result DBHandler_GetValue(cap_string strThingName, cap_string strValueName, SValueInfo **ppstValue);
cap_result DBHandler_GetValueList(IN cap_string strThingName, OUT cap_handle hValueList);
cap_result DBHandler_GetLatestStringValueByServiceKey(IN cap_string strServiceKey,
                                                      OUT cap_string
                                                          strLatestValue);  // ServiceKey : [ThingName].[ValueName]
cap_result DBHandler_GetLatestDoubleValueByServiceKey(
    IN cap_string ServiceKey,
    OUT double *pdbLatestValue);  // ServiceKey : [ThingName].[ValueName]
cap_result DBHandler_GetLatestStringValueByThingAndValue(IN cap_string strThingName, IN cap_string strValueName,
                                                         OUT cap_string strLatestValue);
cap_result DBHandler_GetLatestDoubleValueByThingAndValue(IN cap_string strThingName, IN cap_string strValueName,
                                                         OUT double *pdbLatestValue);

// tag
cap_result DBHandler_AddTag(cap_string strThingName, cap_string strServiceName, cap_string strTagName);
cap_result DBHandler_DeleteTag(cap_string strThingName, cap_string strServiceName, cap_string strTagName);

//----------------------------------------
// middleware related
//----------------------------------------

cap_result DBHandler_ClearMiddlewareDB();
cap_result DBHandler_AddMiddleware(IN cap_string strMiddlewareName, IN cap_string strHierarchy);
cap_result DBHandler_SetMiddlewareAliveness(IN cap_string strMiddlewareName, cap_bool bIsAlive);

cap_result DBHandler_GetMiddlewareHierarchyByName(IN cap_string strMiddlewareName,
                                                  OUT cap_string *pstrMiddlewareHierarhcy);
cap_result DBHandler_GetMiddlewareNameById(IN int id, IN OUT cap_string strMiddlewareName);
cap_result DBHandler_GetMiddlewareNameByThingName(IN cap_string strThingName, IN OUT cap_string strMiddlewareName);
cap_result DBHandler_GetMiddlewareNameBySuperThingName(IN cap_string strSuperThingName,
                                                       IN OUT cap_string strMiddlewareName);
cap_result DBHandler_UpdateMiddlewareLatestTime(IN cap_string strMiddlewareName);
cap_result DBHandler_GenerateMiddlewareAliveInfoArray(IN OUT SMiddlewareAliveInfo **ppstMiddlewareAliveInfoArray,
                                                      IN int *pnArrayLength);

#ifdef __cplusplus
}
#endif

#endif /* DBHANDLER_H_ */
