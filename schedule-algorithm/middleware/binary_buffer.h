#ifndef BinaryBuffer_H_
#define BinaryBuffer_H_

#include "CAPString.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @mainpage SoPIoT Binary Buffer
 *
 * BinaryBuffer is a buffer to save binary Values such as photos, videos.
 */

cap_result BinaryBuffer_Create(OUT cap_handle *phBinaryBuffer);
cap_result BinaryBuffer_Destroy(IN OUT cap_handle *phBinaryBuffer);
cap_result BinaryBuffer_Set(cap_handle hBinaryBuffer, IN cap_string strKey,
                            IN cap_string strEncodedBinary);
cap_result BinaryBuffer_Get(cap_handle hBinaryBuffer, IN cap_string strKey,
                            OUT cap_string strEncodedBinary);
cap_result BinaryBuffer_Delete(cap_handle hBinaryBuffer, IN cap_string strKey);

#ifdef __cplusplus
}
#endif

#endif /* BinaryBuffer_H_ */
