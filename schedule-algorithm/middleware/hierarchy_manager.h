#ifndef HIERARCHYMANAGER_H_
#define HIERARCHYMANAGER_H_

#include "json-c/json_object.h"
#include "json-c/json_tokener.h"
#include "requesting_thread.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _SMiddlewareAliveInfo {
  cap_string strMiddlewareName;
  int nAliveCycle;
  long long llLatestTime;
} SMiddlewareAliveInfo;

typedef struct _SHierarchyManager {
  ESoPHandleId enID;
  cap_bool bCreated;
  cap_handle hEvent;  // wait for the alive checking period.
  cap_handle hLock;
  cap_handle hParentMQTTHandler;
  cap_handle hChildMQTTHandler;
  cap_string strParentBrokerURI;
  cap_string strChildBrokerURI;
  cap_string strMiddlewareName;
  int nAliveCheckingPeriod;
  SMiddlewareAliveInfo* pstMiddlewareAliveInfoArray;
  cap_handle hScheduler;
  cap_handle hRequestQueue;

  cap_handle hRequestHandlingThread;
  cap_handle hSynchronizingThread;
  cap_handle hRequestingThreadHash;
} SHierarchyManager;

cap_result HierarchyManager_HandleServiceArrayJson(SHierarchyManager* pstHierarchyManager,
                                                   json_object* pJsonServiceArray, ESource enFrom, cap_bool* pbUpdated);

cap_result HierarchyManager_Create(OUT cap_handle* phHierarchyManager, IN cap_string strParentBrokerURI,
                                   IN cap_string strChildBrokerURI, IN cap_string strMiddlewareId);
cap_result HierarchyManager_Run(IN cap_handle hHierarchyManager, IN int nAliveCheckingPeriod, IN cap_handle hScheduler);
cap_result HierarchyManager_Join(IN cap_handle hHierarchyManager);
cap_result HierarchyManager_Destroy(IN OUT cap_handle* phHierarchyManager);

CALLBACK cap_result DestroyRequestingThreadHash(IN cap_string strKey, IN void* pData, IN void* pUserData);

#ifdef __cplusplus
}
#endif

#endif  // HIERARCHYMANAGER_H_
