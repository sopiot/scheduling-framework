#ifndef SERVICE_TABLE_H
#define SERVICE_TABLE_H

#include "AppScriptModeler.h"
#include "CAPString.h"
#include "sop_common.h"
#include "task.h"

/**
 * @mainpage SoPIoT Service Table
 *
 * Service Table is a table that is keeping service info (availability, state)
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef enum _EServiceState { SERVICE_STATE_READY, SERVICE_STATE_BUSY, SERVICE_STATE_ERROR } EServiceState;

typedef struct _SServiceInfo {
  EServiceState enState;
  EServiceType enType;
  cap_bool bIsSmall;       // small or big.
  cap_bool bIsSuper;       // super or local.
  cap_bool bIsParallel;    // allow multiple request?
  long long llExecTimeMs;  // execution time in milli seconds.
  long long llEnergyJ;     // consumed energy per an execution.
} SServiceInfo;

typedef struct _SServiceTable {
  // strServiceKey: ThingName.ServiceName
  cap_handle hHash;  // strServiceKey -> SServiceInfo
  cap_handle hLock;
} SServiceTable;

// ServiceInfo
cap_result ServiceInfo_Create(IN EServiceType enType, IN cap_bool bIsSmall, IN cap_bool bIsSuper,
                              IN cap_bool bIsParallel, IN long long llExecTimeMs, IN long long llEnergyJ,
                              OUT SServiceInfo **ppstServiceInfo);
cap_result ServiceInfo_Destroy(IN SServiceInfo **ppstServiceInfo);
cap_result ServiceInfo_Update(IN SServiceInfo *pstServiceInfo, IN EServiceType enType, IN cap_bool bIsSmall,
                              IN cap_bool bIsSuper, IN cap_bool bIsParallel, IN long long llExecTimeMs,
                              IN long long llEnergyJ);

// ServiceTable
cap_result ServiceTable_GetIsParallel(cap_handle hServiceTable, IN cap_string strThingName,
                                      IN cap_string strServiceName, IN OUT cap_bool *pbIsParallel);
cap_result ServiceTable_GetState(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                                 IN OUT EServiceState *penState);
cap_result ServiceTable_SetState(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                                 IN EServiceState enState);
cap_result ServiceTable_SetState_FromExecutionResult(cap_handle hServiceTable, IN SExecutionResult *pstExecutionResult);
cap_result ServiceTable_GetExecTime(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                                    OUT long long *pllExecTimeMs);
cap_result ServiceTable_GetIsSuper(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                                   OUT cap_bool *pbIsSuper);
cap_result ServiceTable_GetIsSmall(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                                   OUT cap_bool *pbIsSmall);

cap_result ServiceTable_Put(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                            IN EServiceType enType, IN cap_bool bIsSmall, IN cap_bool bIsSuper, IN cap_bool bIsParallel,
                            IN long long llExecTimeMs, IN long long llEnergyJ);
cap_result ServiceTable_Get(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                            OUT SServiceInfo **ppstServiceInfo);
cap_result ServiceTable_Delete(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName);
cap_result ServiceTable_Update(cap_handle hServiceTable, IN cap_string strThingName, IN cap_string strServiceName,
                               IN EServiceState enState);
cap_result ServiceTable_Create(OUT cap_handle *phServiceTable);
cap_result ServiceTable_Destroy(IN OUT cap_handle *phServiceTable);

#ifdef __cplusplus
}
#endif

#endif /* SERVICE_TABLE_H */
