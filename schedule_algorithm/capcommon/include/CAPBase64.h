/*
 * CAPBase64.h
 *
 *  Created on: 2016. 4. 22.
 *      Author: kangdongh
 */

#ifndef CAPBASE64_H_
#define CAPBASE64_H_

#include <cap_common.h>

#ifdef __cplusplus
extern "C"
{
#endif

/** 
 * @brief return a base64 encoded length.
 *
 * @param nLen a length of the data.
 * @param pnEncodedLen [out] the length of the endcoded data.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM
 */
cap_result CAPBase64_Encode_Len(IN int nLen, OUT int *pnEncodedLen);

/** 
 * @brief Apply Base64 encoding
 *  
 * @param pData a pointer of the input stream(data) to encode
 * @param nDataLen a length of the input string(data)
 * @param [out] ppEncodedData a pointer of the encoded data array 
 * @param [out] pnEncodedLen a length of the encoded data
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_INTERNAL_FAIL, @ref ERR_CAP_OUT_OF_MEMORY
 */
cap_result CAPBase64_Encode(IN char *pData, IN int nDataLen, OUT char** ppEncodedData, OUT int* pnEncodedLen);

/** 
 * @brief get a decoded length of encoded data.
 *  
 * @param pEncodedData A pointer of the encoded data.
 * @param pnDecodedLen [out] a length of the decoded data
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */

cap_result CAPBase64_Decode_Len(IN char *pEncodedData, OUT int* pnDecodedLen);


/** 
 * @brief Decode a base64-encoded data.
 *  
 * @param pEncodedData a pointer of the Encoded data
 * @param ppDecodedData [out] a pointer for the Decoded data array
 * @param pnDecodedLen [out] the size of the decoded data
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, @ref ERR_CAP_INTERNAL_FAIL
 */

cap_result CAPBase64_Decode(IN char *pEncodedData, OUT char **ppDecodedData, OUT int *pnDecodedLen);

#ifdef __cplusplus
}
#endif


#endif /* CAPBASE64_H_ */
