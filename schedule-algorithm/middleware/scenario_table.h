#ifndef SCENARIO_TABLE_H
#define SCENARIO_TABLE_H

#include "CAPHash.h"
#include "CAPString.h"
#include "sop_common.h"

/**
 * @mainpage SoPIoT Scenario Table
 *
 * Scenario Table is a table that is keeping scenario info (graph, state)
 */

#ifdef __cplusplus
extern "C" {
#endif

typedef enum _EScenarioState {
  SCENARIO_STATE_CREATED,
  SCENARIO_STATE_SCHEDULING,
  SCENARIO_STATE_INITIALIZED,
  SCENARIO_STATE_RUNNING,
  SCENARIO_STATE_EXECUTING,
  SCENARIO_STATE_STUCKED,
  SCENARIO_STATE_COMPLETED,
} EScenarioState;

typedef struct _SScenarioInfo {
  EScenarioState enState;
  cap_handle hScenarioModel;
  int nPeriodMs;
  int nPriority;
} SScenarioInfo;

typedef struct _SScenarioTable {
  cap_handle hHash;  // ScenarioName -> SScenarioInfo
  cap_handle hLock;
} SScenarioTable;

// ScenarioInfo
cap_result ScenarioInfo_Create(IN cap_handle hScenarioModel, IN int nPriority,
                               OUT SScenarioInfo **ppstScenarioInfo);
cap_result ScenarioInfo_Update(IN cap_handle hScenarioInfo, IN int nPriority,
                               IN cap_handle hScenarioModel);
cap_result ScenarioInfo_Destroy(OUT SScenarioInfo **ppstScenarioInfo);

// ScenarioTable
cap_result ScenarioTable_Create(OUT cap_handle *phScenarioTable);
cap_result ScenarioTable_Destroy(IN OUT cap_handle *phScenarioTable);

cap_result ScenarioTable_Put(cap_handle hScenarioTable,
                             IN cap_string strScenarioName,
                             IN cap_handle hScenarioModel, IN int nPriority);
cap_result ScenarioTable_GetCopy(cap_handle hScenarioTable,
                                 IN cap_string strScenarioName,
                                 OUT SScenarioInfo **ppstDstScenarioInfo);
cap_result ScenarioTable_Get(cap_handle hScenarioTable,
                             IN cap_string strScenarioName,
                             OUT SScenarioInfo **ppstScenarioInfo);
cap_result ScenarioTable_GetPeriod(cap_handle hScenarioTable,
                                   IN cap_string strScenarioName,
                                   OUT int *pnPeriodMs);
cap_result ScenarioTable_Delete(cap_handle hScenarioTable,
                                IN cap_string strScenarioName);

cap_result ScenarioTable_GetState(cap_handle hScenarioTable,
                                  IN cap_string strScenarioName,
                                  IN OUT EScenarioState *penState);
cap_result ScenarioTable_SetState(cap_handle hScenarioTable,
                                  IN cap_string strScenarioName,
                                  IN EScenarioState enState);
cap_result ScenarioTable_ClearExecution(cap_handle hScenarioTable,
                                        IN cap_string strScenarioName);

cap_result ScenarioTable_Traverse(cap_handle hScenarioTable,
                                  IN CbFnCAPHash fnCallback,
                                  IN void *pUserData);

cap_result ScenarioTable_Lock(cap_handle hScenarioTable);
cap_result ScenarioTable_Unlock(cap_handle hScenarioTable);

#ifdef __cplusplus
}
#endif

#endif /* SCENARIO_TABLE_H */
