/*
 * CAPKeyValue.h
 *
 *  Created on: 2015. 8. 28.
 *      Author: chjej202
 */

#ifndef CAPKEYVALUE_H_
#define CAPKEYVALUE_H_

#include <cap_common.h>
#include <CAPString.h>

/** 
 * @brief Create a key-value handle.
 *  
 * This function creates a hash with @a nNumOfBuckets size of buckets.
 *
 * @param nBucketNum The number of buckets used in key-value pair.
 * @param phKeyValue [out] a key-value handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPKeyValue_Create(IN int nBucketNum, OUT cap_handle *phKeyValue);


/** 
 * @brief Destroy a key-value handle.
 *  
 * This function destroys a key-value data structure.
 *
 * @param phKeyValue a key-value handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPKeyValue_Destroy(IN OUT cap_handle *phKeyValue);


/** 
 * @brief Add a key with its value.
 *  
 * This function adds a key-value pair. \n
 * If the key is already inserted in the key-value, the function will return an error.
 *
 * @param hKeyValue a key-value handle.
 * @param strKey a key to be add.
 * @param strValue a value to be add.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM,  \n
 *         @ref ERR_CAP_DUPLICATED.
 */
cap_result CAPKeyValue_Add(cap_handle hKeyValue, IN cap_string strKey, IN cap_string strValue);


/** 
 * @brief Delete a key with its value.
 *  
 * This function removes a key and its value. \n
 * If the key is not found in the key-value data structure, the function returns no error.
 *
 * @param hKeyValue a key-value handle.
 * @param strKey a key to be deleted.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPKeyValue_Remove(cap_handle hKeyValue, IN cap_string strKey);


/** 
 * @brief Set a key with its value.
 *  
 * This function sets a key-value pair. \n
 * If the key is already inserted in the key-value, the function only overwrites value.
 *
 * @param hKeyValue a key-value handle.
 * @param strKey a key to be set.
 * @param strValue a value to be set.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPKeyValue_SetValueByKey(cap_handle hKeyValue, IN cap_string strKey, IN cap_string strValue);


/** 
 * @brief Get value by key.
 *  
 * This function gets value of corresponding key. \n
 * If the key is not found in the hash data structure, the function returns an error.
 *
 * @param hKeyValue a key-value handle.
 * @param strKey a key to find.
 * @param strValue a retrieved value.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NOT_FOUND.
 */
cap_result CAPKeyValue_GetValueByKey(cap_handle hKeyValue, IN cap_string strKey, IN OUT cap_string strValue);


/** 
 * @brief Clear all key-value data.
 *  
 * This function removes all the key-value strings.
 *
 * @param hKeyValue a key-value handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPKeyValue_RemoveAll(cap_handle hKeyValue);


/** 
 * @brief Read key-value strings from buffer and inserts into key-value data structure.
 *  
 * This function reads key-value strings from buffer and fills key-value data \n
 * into the data structure. The buffer must be written like "key = value" \n
 * with multiple lines. For example:
 *
 *     name=James
 *     age=24
 *     grade=B0
 *
 * Spaces between key and =(equal), =(equal) and value are ignored. \n
 * keys and values are also trimmed when they insert into the key-value data structure. \n
 * If there is any duplicated key already inside key-value data structure, \n
 * the function returns an error.
 *
 * @param hKeyValue a key-value handle.
 * @param pszBuffer a source buffer which contains key=value strings.
 * @param nBufSize the size of source buffer.
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_DATA, \n
 *         @ref ERR_CAP_DUPLICATED.
 */
cap_result CAPKeyValue_ReadFromBuffer(cap_handle hKeyValue, IN char *pszBuffer, IN int nBufSize);


/** 
 * @brief Write data in key-value data structure to cap_string
 *  
 * This function writes the data in key-value data structure to cap_string with speicific format. \n
 * The format written to cap_string is "key = value" with multiple lines. \n
 * Example can be referred from the description of @ref CAPKeyValue_ReadFromBuffer. \n
 * The string already in the @a strToString are removed and replaced to the output of key-value string \n
 * after this operation.
 * 
 * @param hKeyValue a key-value handle.
 * @param strToString a destination cap_string which stores cap_string data
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPKeyValue_WriteToString(cap_handle hKeyValue, IN OUT cap_string strToString);


/** 
 * @brief Duplicate key-value data structure
 *  
 * This function duplicates @a hSrcKeyValue to @a hDstKeyValue. \n
 * All the key-value data already included in @a hDstKeyValue will be removed and \n
 * replaced to the data of @a hSrcKeyValue.
 * 
 * @param hDstKeyValue a destination key-value handle.
 * @param hSrcKeyValue a source key-value handle
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_NO_DATA.
 */
cap_result CAPKeyValue_Duplicate(cap_handle hDstKeyValue, cap_handle hSrcKeyValue);

#endif /* CAPKEYVALUE_H_ */
