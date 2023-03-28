#ifndef SCHEDULE_TABLE_H
#define SCHEDULE_TABLE_H

#include "AppScriptModeler.h"
#include "CAPString.h"
#include "service_table.h"
#include "sop_common.h"

/**
 * @mainpage SoPIoT Schedule Table
 *
 * Schedule Table is a table that is keeping schedule info
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef enum _EEScheduleState {
  SCHEDULE_STATE_READY,
  SCHEDULE_STATE_DONE,
  SCHEDULE_STATE_ERROR
} EScheduleState;

typedef struct _SScheduleInfo {
  EServiceType enServiceType;
  cap_handle hMappedThingNameList;
  EScheduleState enState;
} SScheduleInfo;

typedef struct _SScheduleTable {
  // hScheduleMap: strScheduleKey -> SScheduleInfo
  // strScheduleKey:
  //  strPrimaryIdentifier.strServiceName |
  //  strMiddlewareName.strSuperServiceName
  cap_handle hHash;  // strScenarioName -> hScheduleMap
  cap_handle hLock;
} SScheduleTable;

CALLBACK cap_result DestroyScheduleInfoHash(IN cap_string strKey,
                                            IN void *pData, IN void *pUserData);

cap_result ScheduleInfo_Create(IN EScheduleState enState,
                               IN EServiceType enServiceType,
                               OUT SScheduleInfo **ppstScheduleInfo);
cap_result ScheduleInfo_Destroy(IN SScheduleInfo **ppstScheduleInfo);

cap_result ScheduleMap_Copy(IN cap_handle hSrcScheduleMap,
                            OUT cap_handle *phDstScheduleMap);

cap_result ScheduleTable_Lock(cap_handle hScheduleTable);
cap_result ScheduleTable_Unlock(cap_handle hScheduleTable);
cap_result ScheduleTable_LoadScenario(cap_handle hScheduleTable,
                                      IN cap_handle hScenarioModel);

cap_result ScheduleTable_AddScheduleMap(cap_handle hScheduleTable,
                                        IN cap_string strScenarioName,
                                        IN cap_handle hScheduleMap);
cap_result ScheduleTable_DeleteScheduleMap(cap_handle hScheduleTable,
                                           IN cap_string strScenarioName);
cap_result ScheduleTable_GetScheduleMap(cap_handle hScheduleTable,
                                        IN cap_string strScenarioName,
                                        OUT cap_handle *phScheduleMap);
cap_result ScheduleTable_GetMappedThingNameListRef(
    cap_handle hScheduleTable, IN cap_string strScenarioName,
    IN cap_string strScheduleKey, OUT cap_handle *phMappedThingNameListRef);
cap_result ScheduleTable_GetMappedThingNameList(
    cap_handle hScheduleTable, IN cap_string strScenarioName,
    IN cap_string strScheduleKey, OUT cap_handle *phMappedThingNameList);
cap_result ScheduleTable_AddSuperThingRequest(
    cap_handle hScheduleTable, IN cap_string strScenarioName,
    IN cap_string strIdentifier, IN cap_string strServiceName,
    IN cap_handle hMappedThingNameList, IN EServiceType enServiceType);

cap_result ScheduleTable_SetState(cap_handle hScheduleTable,
                                  IN cap_string strScenarioName,
                                  IN cap_string strIdentifier,
                                  IN cap_string strServiceName,
                                  IN EScheduleState enState);
cap_result ScheduleTable_Get(cap_handle hScheduleTable,
                             IN cap_string strScenarioName,
                             IN cap_string strIdentifier,
                             IN cap_string strServiceName,
                             OUT SScheduleInfo **ppstScheduleInfo);
cap_result ScheduleTable_Delete(cap_handle hScheduleTable,
                                IN cap_string strScenarioName,
                                IN cap_string strIdentifier,
                                IN cap_string strServiceName);

cap_result ScheduleTable_CancelByScenario(cap_handle hScheduleTable,
                                          IN cap_handle hScenarioTable,
                                          IN cap_handle hServiceTable,
                                          IN cap_string strScenarioName);
cap_result ScheduleTable_CancelByService(cap_handle hScheduleTable,
                                         IN cap_handle hScenarioTable,
                                         IN cap_handle hServiceTable,
                                         IN cap_string strThingName,
                                         IN cap_string strServiceName);
cap_result ScheduleTable_CurrUtilization(cap_handle hScheduleTable,
                                         IN cap_handle hScenarioTable,
                                         IN cap_handle hServiceTable,
                                         IN cap_string strThingName,
                                         IN cap_string strFunctionName,
                                         IN double *pdbCurrUtilization);

cap_result ScheduleTable_TraverseScenario(cap_handle hScheduleTable,
                                          IN cap_string strScenarioName,
                                          IN CbFnCAPHash fnCallback,
                                          IN void *pUserData);

cap_result ScheduleTable_Create(OUT cap_handle *phScheduleTable);
cap_result ScheduleTable_Destroy(IN OUT cap_handle *phScheduleTable);

#ifdef __cplusplus
}
#endif

#endif /* SCHEDULE_TABLE_H */
