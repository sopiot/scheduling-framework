#ifndef INFOMANAGER_H_
#define INFOMANAGER_H_

#include <MQTTClient.h>
#include <mqtt_utils.h>

#include "CAPThread.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _SInfoManager {
  ESoPHandleId enID;
  cap_bool bCreated;
  int nSocketListeningPort;
  cap_handle hSocketAcceptingThread;
  cap_handle hValueTopicSubscribingThread;
  cap_handle hMessageSendingThread;
  cap_handle hMQTTHandler;
  cap_handle hServerSocket;
  cap_handle hValueTopicQueue;
  cap_handle hPlatformDataQueue;
  cap_handle hSocketThreadList;
  cap_handle hTerminatedSocketThreadList;
  cap_handle hMessageQueueList;
  cap_handle hScheduler;
  cap_handle hLock;
  cap_string strMiddlewareName;
} SInfoManager;

cap_result InfoManager_Create(OUT cap_handle* phInfoManager,
                              IN cap_string strBrokerURI,
                              IN int nSocketListeningPort,
                              cap_string strMiddlewareName);
cap_result InfoManager_Run(IN cap_handle hInfoManager,
                           IN cap_handle hScheduler);
cap_result InfoManager_Join(IN cap_handle hInfoManager);
cap_result InfoManager_Destroy(IN OUT cap_handle* phInfoManager);

#ifdef __cplusplus
}
#endif

#endif /* InfoMANAGER_H_ */
