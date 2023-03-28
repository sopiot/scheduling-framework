#ifndef VALUECACHE_H_
#define VALUECACHE_H_

#include "CAPString.h"
#include "sop_common.h"
#include "thing_info_handler.h"

#ifdef __cplusplus
extern "C" {
#endif

typedef struct _SCachedInfo {
  SValueInfo *pstValueInfo;
  cap_bool bInit;  // whether the value is set or not
  cap_string strValue;
  double dbValue;
  cap_handle hLock;
} SCachedInfo;

typedef struct _SValueCache {
  ESoPHandleId enID;
  cap_handle hIndexHash;
  cap_handle hBinaryBuffer;
  SCachedInfo **ppastCachedInfo;
  int nArraySize;
  int nValueNum;
  int nBucketNum;  // number of bucket(slot) of the hash table
} SValueCache;

cap_result ValueCache_DuplicateIndexHash(cap_handle hCache,
                                         IN OUT cap_handle hIndexHash);

cap_result ValueCache_Create(OUT cap_handle *phCache);
cap_result ValueCache_Destroy(IN OUT cap_handle *phCache);

cap_result ValueCache_Add(cap_handle hCache, IN cap_string strKey,
                          IN SValueInfo stValueInfo);

cap_result ValueCache_UpdateDouble(cap_handle hCache, IN int nIndex,
                                   IN double dbValue);
cap_result ValueCache_UpdateString(cap_handle hCache, IN int nIndex,
                                   IN cap_string strValue);
cap_result ValueCache_UpdateDoubleByKey(cap_handle hCache, IN cap_string strKey,
                                        IN double dbValue);
cap_result ValueCache_UpdateStringByKey(cap_handle hCache, IN cap_string strKey,
                                        OUT cap_string strValue);

cap_result ValueCache_GetDouble(cap_handle hCache, IN int nIndex,
                                OUT double *pdbValue);
cap_result ValueCache_GetString(cap_handle hCache, IN int nIndex,
                                OUT cap_string strValue);

cap_result ValueCache_GetDoubleByKey(cap_handle hCache, IN cap_string strKey,
                                     OUT double *pdbValue);
cap_result ValueCache_GetStringByKey(cap_handle hCache, IN cap_string strKey,
                                     OUT cap_string strValue);

cap_result ValueCache_SetBinaryByKey(cap_handle hCache, IN cap_string strKey,
                                     IN cap_string strEncodedBinary);
cap_result ValueCache_GetBinaryByKey(cap_handle hCache, IN cap_string strKey,
                                     OUT cap_string strEncodedBinary);
cap_result ValueCache_DeleteBinaryByKey(cap_handle hCache,
                                        IN cap_string strKey);

cap_result ValueCache_GetBucketNumber(cap_handle hCache, OUT int *pnBucketNum);
cap_result ValueCache_GetType(cap_handle hCache, IN int nIndex,
                              OUT EValueType *penType);
cap_result ValueCache_GetTypeByKey(cap_handle hCache, IN cap_string strKey,
                                   OUT EValueType *penType);

#ifdef __cplusplus
}
#endif

#endif /* VALUECACHE_H_ */
