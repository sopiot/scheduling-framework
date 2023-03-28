/*
 * CAPHash.h
 *
 *  Created on: 2015. 8. 19.
 *      Author: chjej202
 */

#ifndef CAPHASH_H_
#define CAPHASH_H_

#include <cap_common.h>
#include <CAPString.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef cap_result (*CbFnCAPHash)(IN cap_string strKey, IN void *pData, IN void *pUserData);
typedef cap_result (*CbFnCAPHashDup)(IN cap_string strKey, IN void *pDataSrc, IN void *pUserData, OUT void **ppDataDst);


/** 
 * @brief Create a hash handle.
 *  
 * This function creates a hash with @a nNumOfBuckets size of buckets.
 *
 * @param nNumOfBuckets  The number of buckets used in hash.
 * @param phHash [out] a hash handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPHash_Create(IN int nNumOfBuckets, OUT cap_handle *phHash);


/** 
 * @brief Destroy a hash handle.
 *  
 * This function destroys a hash handle. \n
 * Because hash values can be memory-allocated data, callback function \n
 * for each hash key destruction is also provided. 
 *
 * @param phHash  a hash handle to be destroyed.
 * @param fnDestroyCallback callback function for destroying internal hash values.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPHash_Destroy(IN OUT cap_handle *phHash, IN CbFnCAPHash fnDestroyCallback, IN void *pUserData);


/** 
 * @brief Add a hash key with its value.
 *  
 * This function adds a hash key into the hash data structure. \n
 * If the hash key is already inserted in the hash data structure, the function will return an error.
 *
 * @warning CAPHash only stores the pointer value. \n
 * Please use callback functions of destroy/delete functions and \n
 * delete the pointed data correctly to avoid memory leak.
 *
 *
 * @param hHash a hash handle.
 * @param strKey a hash key to be set.
 * @param pData a hash value to be set.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_DUPLICATED.
 */
cap_result CAPHash_AddKey(cap_handle hHash, IN cap_string strKey, IN void *pData);


/** 
 * @brief Delete a hash key with its value.
 *  
 * This function deletes a hash key and its value. \n
 * If the hash key is not found in the hash data structure, the function returns no error.
 *
 * @param hHash a hash handle.
 * @param strKey a hash key to be deleted.
 * @param fnDestroyCallback callback function for destroying internal hash value.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPHash_DeleteKey(cap_handle hHash, IN cap_string strKey, IN CbFnCAPHash fnDestroyCallback, IN void *pUserData);


/** 
 * @brief Get hash value by hash key.
 *  
 * This function gets hash value of corresponding hash key. \n
 * If the hash key is not found in the hash data structure, the function returns an error.
 *
 * @param hHash a hash handle.
 * @param strKey a hash key to find.
 * @param ppData [out] a retrieved hash value.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NOT_FOUND.
 */
cap_result CAPHash_GetDataByKey(cap_handle hHash, IN cap_string strKey, OUT void **ppData);


/** 
 * @brief Clear all internal hash data.
 *  
 * This function removes all the hash keys and values.
 *
 * @param hHash a hash handle.
 * @param fnDestroyCallback callback function for destroying internal hash value.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPHash_RemoveAll(cap_handle hHash, IN CbFnCAPHash fnDestroyCallback, IN void *pUserData);


/**
 * @brief Retrieve the number of items in the hash.
 *
 * This function retrieves the number of items in the hash.
 *
 * @param hHash a hash handle.
 * @pnItemNum [out] the number of items in the hash.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPHash_GetNumberOfItems(cap_handle hHash, OUT int *pnItemNum);


/** 
 * @brief Traverse all hash data in hash data structure.
 *  
 * This function traverses all the data in hash data structure. \n
 * This function is used for referencing all the data one by one.
 *
 * @param hHash a hash handle.
 * @param fnCallback callback function for handling each hash data.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPHash_Traverse(cap_handle hHash, IN CbFnCAPHash fnCallback, IN void *pUserData);


/** 
 * @brief Copy hash data to another hash data structure.
 *  
 * This function copies all the hash data from @a hSrcHash to @a hDstHash. \n
 * To copy internal hash value, @a fnDataCopyCallback callback function is used. \n
 * The destination hash must not have any data and the source hash must have \n
 * at least one hash data. Otherwise, it retrieves an error.
 *
 *
 * @param hDstHash a destination hash handle.
 * @param hSrcHash a source hash handle.
 * @param fnDataCopyCallback callback function for copying internal hash value of each hash data.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_NOT_EMTPY, 
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPHash_Duplicate(IN OUT cap_handle hDstHash, IN cap_handle hSrcHash, IN CbFnCAPHashDup fnDataCopyCallback, IN void *pUserData);



#ifdef __cplusplus
}
#endif

#endif /* CAPHASH_H_ */
