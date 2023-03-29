#ifndef THINGINFOHANDLER_H_
#define THINGINFOHANDLER_H_

#include "CAPString.h"
#include "json-c/json_object.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

#define THING_DB_ID_NOT_SET (-1)

typedef struct _SValueTag {
  cap_string strValueTagName;
} SValueTag;

typedef struct _SValue {
  cap_string strValueName;
  cap_string strDescription;
  EValueType enType;
  double dbMinValue;
  double dbMaxValue;
  char* pszFormat;
  SValueTag* pstValueTags;
  int nValueTagNum;
  cap_bool bIsPrivate;
} SValueInfo;

typedef struct _SArgument {
  cap_string strArgumentName;
  EValueType enArgumentType;
  int nOrder;
  double dbArgMinValue;
  double dbArgMaxValue;
} SArgument;

typedef struct _SFunctionTag {
  cap_string strFunctionTagName;
} SFunctionTag;

typedef struct _SFunction {
  cap_string strFunctionName;
  cap_string strDescription;
  cap_bool bUseArgument;
  SArgument* pstArguments;
  SFunctionTag* pstFunctionTags;
  int nArgumentNum;
  int nFunctionTagNum;
  EValueType enReturnType;
  cap_bool bIsPrivate;
  cap_bool bIsAvailable;
  long long llExecTimeMs;
  long long llEnergyJ;
} SFunctionInfo;

typedef struct _SThingInfo {
  cap_string strThingName;
  int nAliveCycle;
  int nValueNum;
  SValueInfo* pstValueInfos;
  int nFunctionNum;
  SFunctionInfo* pstFunctionInfos;
  cap_bool bIsSmall;
  cap_bool bIsAlive;
  cap_bool bIsSuper;
  cap_bool bIsParallel;
} SThingInfo;

cap_result ThingInfoHandler_PutToServiceTable(IN SThingInfo* pstThingInfo,
                                              IN cap_handle hServiceTable);
cap_result ThingInfoHandler_AddValueToValueCache(IN SThingInfo* pstThingInfo,
                                                 IN cap_handle hValueCache);
cap_result ThingInfoHandler_Create(IN json_object* pJsonThing,
                                   OUT SThingInfo** ppstThingInfo);
cap_result ThingInfoHandler_Destroy(IN OUT SThingInfo** ppstThing);

cap_result ThingInfo_Destroy(IN SThingInfo** ppstThingInfo);
cap_result FunctionInfo_Destroy(IN SFunctionInfo** ppstFunctionInfo);
cap_result ValueInfo_Destroy(IN SValueInfo** ppstValueInfo);

#ifdef __cplusplus
}
#endif

#endif /* THINGINFOHANDLER_H_ */
