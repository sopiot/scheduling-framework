#ifndef SCENARIO_RUNNER_UTILS_H_
#define SCENARIO_RUNNER_UTILS_H_

#include "AppScriptModeler.h"
#include "cap_common.h"
#include "thing_info_handler.h"

CALLBACK cap_result DestroyHashData(IN cap_string strKey, IN void *pData, IN void *pUserData);
CALLBACK cap_result DestroyConditionList(IN int nOffset, IN void *pData, IN void *pUserData);
CALLBACK cap_result DestroyExecutionResultQueue(IN void *pData, IN void *pUserData);
CALLBACK cap_result DestroyScheduleResultQueue(IN void *pData, IN void *pUserData);
CALLBACK cap_result DestroyConditionListQueue(IN void *pData, IN void *pUserData);
CALLBACK cap_result DuplicateConditionList(IN int nOffset, IN void *pDataSrc, IN void *pUserData, OUT void **ppDataDst);
cap_result ConvertTimeToMilliseconds(double dbTimeValue, ETimeUnit enTimeUnit, long long *pllMilliseconds);

#endif  // SCENARIO_RUNNER_UTILS_H_