#ifndef MIDDLEWARE_ON_SN_MESSAGE_H_
#define MIDDLEWARE_ON_SN_MESSAGE_H_

#include "CAPString.h"
#include "cap_common.h"

CALLBACK cap_result DestroySNFunctionInfoList(IN int nOffset, IN void *pData,
                                              IN void *pUserData);
CALLBACK cap_result DestroySNValueInfoList(IN int nOffset, IN void *pData,
                                           IN void *pUserData);

cap_result ThingManager_OnSNMessage(IN cap_handle hThingManager,
                                    IN cap_handle hTopicItemList,
                                    IN char *pszPayload,
                                    OUT cap_bool *pbIsFinished);

cap_result GetAggregatedSNRegisterInfo(cap_handle hSNRegisterInfoHash,
                                       cap_string strThingName,
                                       char **ppszAggregatedPayload);

#endif  // MIDDLEWARE_ON_SN_MESSAGE_H_