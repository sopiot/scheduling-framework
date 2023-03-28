/*
 * CAPThread.h
 *
 *  Created on: 2015. 5. 19.
 *      Author: chjej202
 */

#ifndef CAPTHREAD_H_
#define CAPTHREAD_H_

#include "cap_common.h"

#ifdef __cplusplus
extern "C"
{
#endif


#ifdef HAVE_PTHREAD
#include <pthread.h>

typedef pthread_t cap_tid;
#else
typedef long int cap_tid;
#endif

typedef void * (*FnNativeThread)(IN void *pData);

#define CAP_THREAD_HEAD void *
#define CAP_THREAD_END	return NULL

/** 
 * @brief Create a thread.
 *  
 * This function creates a thread.
 * 
 * @param fnThreadRoutine a routine running on a thread.
 * @param pUserData data passed to a thread.
 * @param phThread [out] a thread handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPThread_Create(IN FnNativeThread fnThreadRoutine, IN void *pUserData, OUT cap_handle *phThread);

/** 
 * @brief Join a thread and destroy a thread handle.
 *  
 * This function joins a thread and destroy a thread handle.
 * 
 * @param phThread a thread handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_INTERNAL_FAIL.
 */
cap_result CAPThread_Destroy(IN OUT cap_handle *phThread);


/** 
 * @brief Get current thread ID.
 *  
 * This function retrieves a current thread ID.
 *
 * @return current thread ID.
 */
cap_tid CAPThread_GetCurThreadID();

/** 
 * @brief Yield current thread to other thread.
 *  
 * This function is a simple wrap-up function for sched_yield()
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -@ref ERR_CAP_INTERNAL_FAIL.
 */

cap_result CAPThread_Yield();
#ifdef __cplusplus
}
#endif


#endif /* CAPTHREAD_H_ */
