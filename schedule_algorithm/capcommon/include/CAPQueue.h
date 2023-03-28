/*
 * CAPQueue.h
 *
 *  Created on: 2015. 5. 19.
 *      Author: chjej202
 */

#ifndef CAPQUEUE_H_
#define CAPQUEUE_H_

#include <cap_common.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef cap_result (*CbFnQueueTraverse)(IN void *pData, IN void *pUserData);

/** 
 * @brief Create a queue.
 *  
 * This function creates a FIFO queue handle.
 *
 * @param phQueue [out] a queue handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPQueue_Create(OUT cap_handle *phQueue);


/** 
 * @brief Exit a blocked queue.
 *  
 * This function exits a blocked queue. \n
 * This function is used when the program or working thread is going to be terminated.
 *
 * @param hQueue a queue handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPQueue_SetExit(cap_handle hQueue);


/** 
 * @brief Put data into queue.
 *  
 * This function puts data into a queue.
 *
 * @param hQueue a queue handle.
 * @param pData data to put.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPQueue_Put(cap_handle hQueue, IN void *pData);

/** 
 * @brief Get data from queue.
 *  
 * This function gets data into a queue. Because this is a FIFO-queue, first-come data is retrieved. \n
 * Retrieved data is removed from the queue. \n
 * If @a bBlocked is TRUE, the function is blocked inside until queue is not empty. \n
 * If @a bBlocked is FALSE, the function retrieves @ref ERR_CAP_NO_DATA when the queue is empty. \n
 * @ref ERR_CAP_SUSPEND can be returned when @ref CAPQueue_SetExit is called.
 *
 * @param hQueue a queue handle.
 * @param bBlocked wait when the queue is empty or not.
 * @param ppData [out] retrieved data.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_MUTEX_ERROR. \n
 *         @ref ERR_CAP_NO_DATA is retrieved if the queue is empty for non-blocking get. \n
 *         @ref ERR_CAP_SUSPEND is retrieved when @ref CAPQueue_SetExit is called.
 */
cap_result CAPQueue_Get(cap_handle hQueue, IN cap_bool bBlocked, OUT void **ppData);

/**
 * @brief Get data from queue with timeout limit
 * 
 * This functions gets data from a queue in a time range. 
 * @param hQueue a queue handle.
 * @param llTimeoutMs how long the queue will wait for the data
 * @param ppData [out] retrieved data.
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - \n
 *         @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_MUTEX_ERROR \n
 *         @ref ERR_CAP_NO_DATA is retrieved if the queue is empty for non-blocking get. \n
 *         @ref ERR_CAP_SUSPEND is retrieved when @ref CAPQueue_SetExit is called.
 */
cap_result CAPQueue_GetWithTimeout(cap_handle hQueue, IN long long llTimeoutMs,
                        OUT void **ppData);
                        
/** 
 * @brief Retrieve current queue size.
 *  
 * This function retrieves the number of items in queue.
 *
 * @param hQueue a queue handle.
 * @param pnLength [out] the number items in queue.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPQueue_GetLength(cap_handle hQueue, OUT int *pnLength);

// Traverse all the queue (not implemented yet)
//cap_result CAPQueue_Traverse(cap_handle hQueue, IN CbFnQueueTraverse fnTraverse, IN void *pUserData);



/**
 * @brief Remove all items in the queue.
 *
 * This function removes all items in the queue.
 * In addition, it also clears exit flag set by CAPQueue_SetExit.
 *
 * @param hQueue a queue handle.
 * @param fnCallbackDestroy callback function for destroying internal queue data.
 * @param pUsrData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPQueue_RemoveAll(cap_handle hQueue, CbFnQueueTraverse fnCallbackDestroy, void *pUsrData);


/** 
 * @brief Destroy a queue handle.
 *  
 * This function destroys a queue.
 *
 * @param phQueue a queue handle to be destroyed.
 * @param fnCallbackDestroy callback function for destroying internal queue data.
 * @param pUsrData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE.
 */
cap_result CAPQueue_Destroy(IN OUT cap_handle *phQueue, IN CbFnQueueTraverse fnCallbackDestroy, IN void *pUsrData);


#ifdef __cplusplus
}
#endif



#endif /* CAPQUEUE_H_ */
