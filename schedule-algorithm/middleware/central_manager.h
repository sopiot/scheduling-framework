#ifndef CENTRALMANAGER_H_
#define CENTRALMANAGER_H_

#include "CAPString.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _SConfigData {
  char *pszMiddlewareName;

  // connect
  char *pszParentBrokerURI;
  char *pszBrokerURI;
  int nSocketListeningPort;
  int nAliveCheckingPeriod;

  // database
  char *pszMainDBFilePath;
  char *pszValueLogDBFilePath;

  // logger
  int nLogLevel;
  cap_string strLogFilePath;
  int nLogMaxSize;
  int nLogBackupNum;
} SConfigData;

typedef struct _SCentralManager {
  ESoPHandleId enID;
  cap_string strMiddlewareName;

  cap_handle hScheduler;

  cap_handle hHierarchyManager;
  cap_handle hScenarioManager;
  cap_handle hThingManager;
  cap_handle hInfoManager;
} SCentralManager;

cap_result CentralManager_Create(OUT cap_handle *phCentralManager,
                                 IN SConfigData *pstConfigData);
cap_result CentralManager_Execute(IN cap_handle hCentralManager,
                                  IN SConfigData *pstConfigData);
cap_result CentralManager_Destroy(IN OUT cap_handle *phCentralManager);

#ifdef __cplusplus
}
#endif

#endif /* CENTRALMANAGER_H_ */
