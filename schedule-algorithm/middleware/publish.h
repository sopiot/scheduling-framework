#ifndef _PUBLISH_H_
#define _PUBLISH_H_

#include "CAPString.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

cap_result PublishCPTraverse(IN cap_handle hHandler, IN cap_string strRequester,
                             IN cap_string strMiddlewareName,
                             IN cap_string strPrefix, IN int nLevel);
cap_result PublishPCTraverse(IN cap_handle hHandler, IN cap_string strRequester,
                             IN cap_string strPrefix, IN int nLevel);
cap_result PublishMETreeLevel(IN cap_handle hHandler, IN cap_string strPrefix,
                              IN cap_string strMiddlewareName,
                              IN int nTreeLevel);
cap_result PublishMENotify(IN cap_handle hHandler, IN cap_string strPrefix,
                           IN cap_string strRequesterName);
cap_result PublishServiceList(IN cap_handle hHandler, IN EDestination eDst);
cap_result PublishScenarioList(IN cap_handle hHandler, IN cap_handle hScheduler,
                               IN cap_string strPrefix,
                               IN cap_string strRequesterName);
cap_result PublishServiceListResult(IN cap_handle hHandler,
                                    IN cap_string strProtocol,
                                    IN cap_string strRequesterName,
                                    IN EDestination eDst);
cap_result PublishSync(IN cap_handle hParentMQTTHandler,
                       IN cap_handle hChildMQTTHandler);
cap_result PublishBinaryResult(IN cap_handle hMQTTHandler,
                               IN cap_string strPrefix, IN char *pszThingName,
                               IN char *pszValueName);
cap_result PublishScenarioResult(IN cap_handle hHandler, IN cap_string strTopic,
                                 IN cap_string strScenarioName,
                                 IN EScheduleStatusType enScheduleStatus,
                                 IN int nErrorCode,
                                 IN cap_string strErrorString);
cap_result PublishRegisterResult(IN cap_handle hHandler, IN cap_string strTopic,
                                 IN int nErrorCode,
                                 IN cap_string strMiddlewareName);
cap_result PublishErrorCode(IN cap_handle hHandler, IN cap_string strTopic,
                            IN int nErrorCode, IN cap_string strErrorString);
cap_result TossMessage(IN cap_handle hHandler, IN cap_handle hTopicItemList,
                       IN char *pszPayload, IN int nPayloadLen);

#ifdef __cplusplus
}
#endif

#endif /* _PUBLISH_H_ */