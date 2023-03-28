/*
 * CAPThreadLock.h
 *
 *  Created on: 2015. 5. 19.
 *      Author: chjej202
 */

#ifndef CAPTHREADLOCK_H_
#define CAPTHREADLOCK_H_

#include "cap_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

/** 
 * @brief Create a thread lock.
 *  
 * This function creates thread lock which is based on pthread lock.
 * 
 * @param phLock [out] a lock handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadLock_Create(OUT cap_handle *phLock);


/** 
 * @brief Acquire a thread lock.
 *  
 * This function acquires a lock.
 * 
 * @param hLock a lock handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadLock_Lock(cap_handle hLock);


/** 
 * @brief Release a thread lock.
 *  
 * This function releases a lock.
 * 
 * @param hLock a lock handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadLock_Unlock(cap_handle hLock);


/** 
 * @brief Destroy a thread lock handle.
 *  
 * This function destroys a thread lock.
 * 
 * @param phLock a lock handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_MUTEX_ERROR.
 */
cap_result CAPThreadLock_Destroy(IN OUT cap_handle *phLock);

#ifdef __cplusplus
}
#endif


#endif /* CAPTHREADLOCK_H_ */
