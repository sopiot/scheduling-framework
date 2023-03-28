#ifndef THINGMANAGER_H_
#define THINGMANAGER_H_

#include "CAPThread.h"
#include "MQTTClient.h"
#include "central_manager.h"
#include "mqtt_utils.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

#define MQTT_CLIENT_DISCONNECT_TIMEOUT (10000)
#define MQTT_RECEIVE_TIMEOUT (3000)
#define SN_REGISTER_INFO_HASH_BUCKET_NUM (1023)

typedef struct _SSNValueInfo {
  cap_string strName;
  cap_string strType;
  cap_string strMin;
  cap_string strMax;
  cap_handle hTagList;
} SSNValueInfo;

typedef struct _SSNArgumentInfo {
  cap_string strName;
  cap_string strType;
  cap_string strMin;
  cap_string strMax;
} SSNArgumentInfo;

typedef struct _SSNFunctionInfo {
  cap_string strName;
  cap_string strReturnType;
  cap_handle hTagList;
  cap_handle hArgumentList;
} SSNFunctionInfo;

typedef struct _SSNRegisterInfo {
  cap_string strThingName;
  cap_string strAliveCycle;
  cap_handle hFunctionInfoList;
  cap_handle hValueInfoList;
} SSNRegisterInfo;

typedef struct _SThingAliveInfo {
  cap_string strThingName;
  int nAliveCycle;
  long long llLatestTime;
} SThingAliveInfo;

typedef struct _SThingManager {
  ESoPHandleId enID;
  cap_bool bCreated;
  cap_handle hEvent;
  cap_handle hMQTTHandler;

  int nAliveCheckingPeriod;
  SThingAliveInfo* pstThingAliveInfoArray;
  cap_handle hAliveHandlingThread;

  cap_handle hValueTopicQueue;
  cap_handle hPlatformDataQueue;
  cap_handle hHierarchyManager;

  cap_handle hScheduler;

  cap_handle hSNRegisterInfoHash;
  cap_string strMiddlewareName;
} SThingManager;

cap_result ThingManager_Create(OUT cap_handle* phThingManager,
                               IN cap_string strBrokerURI,
                               IN cap_handle hHierarchyManager,
                               IN cap_string strMiddlewareName);
cap_result ThingManager_Run(IN cap_handle hThingManager,
                            IN int nAliveCheckingPeriod,
                            IN cap_handle hValueTopicQueue,
                            IN cap_handle hPlatformDataQueue,
                            IN cap_handle hScheduler);
cap_result ThingManager_Join(IN cap_handle hThingManager);
cap_result ThingManager_Destroy(IN OUT cap_handle* phThingManager);

#ifdef __cplusplus
}
#endif

#endif /* THINGMANAGER_H_ */
