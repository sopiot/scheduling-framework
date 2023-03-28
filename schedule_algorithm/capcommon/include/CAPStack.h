/*
 * CAPHash.h
 *
 *  Created on: 2015. 8. 19.
 *      Author: chjej202
 */

#ifndef CAPSTACK_H_
#define CAPSTACK_H_

#include <cap_common.h>
#include <CAPString.h>
#include <CAPLinkedList.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef cap_result (*CbFnCAPStack)(IN void *pData, IN void *pUserData);
typedef CbFnCAPLinkedListDup CbFnCAPStackDup;

/**
 * @brief Create a stack handle.
 *
 * This function creates a stack.
 *
 * @param phStack [out] a stack handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPStack_Create(OUT cap_handle *phStack);


/**
 * @brief Add data into the stack.
 *
 * This function pushes data into the stack \n
 *
 * @warning CAPStack only stores the pointer value. \n
 * Please use callback functions on destroy function and \n
 * delete the pointed data correctly to avoid memory leak.
 *
 * @param hStack a stack handle.
 * @param pData data to be pushed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPStack_Push(cap_handle hStack, IN void *pData);


/**
 * @brief Pop data from the stack.
 *
 * This function retrieves recently-pushed stack data and removes \n
 * the item from the stack. \n
 * The length of the stack is decreased after calling this function\n
 * because data is popped out from the stack.
 *
 * @warning Popped data is no longer managed by the stack, so memory \n
 * free is needed on that data if the popped data is memory-allocated.
 * @warning If the stack is empty, the function will return @ref ERR_CAP_NO_DATA.
 *
 * @param hStack a stack handle.
 * @param ppData [out] popped data.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPStack_Pop(cap_handle hStack, OUT void **ppData);

/**
 * @brief take a peek of a top of stack handle.
 * 
 * This function retrieves recently-pushed stack data \n
 *
 * @warning Top function does not remove data from stack, it just takes a peek of it \n
 * @warning If the stack is empty, the function will return @ref ERR_CAP_NO_DATA.
 *
 * @param hStack a stack handle.
 * @param ppData [out] popped data.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPStack_Top(cap_handle hStack, OUT void **ppData);

/**
 * @brief Duplicate a stack.
 *
 * This function copies all the data from @a hSrcStack to @a hDstStack. \n
 * To copy each internal data in the stack item, @a fnCallback callback function is used. \n
 * The destination stack must not have any item, and the source stack must have \n
 * at least one item. Otherwise, it retrieves an error.
 *
 * @param hDstStack a destination stack handle.
 * @param hSrcStack a source stack handle.
 * @param fnCallback callback function for copying internal data of each stack item.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_NOT_EMTPY,
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPStack_Duplicate(cap_handle hDstStack, cap_handle hSrcStack,
                                IN CbFnCAPStackDup fnCallback, IN void *pUserData);

/**
 * @brief Get the number of elements in the stack.
 *
 * This function retrieves the number of elements in the stack.
 *
 * @param hStack a stack handle.
 * @param pnLength [out] the number of elements in the stack.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPStack_Length(cap_handle hStack, OUT int *pnLength);


/**
 * @brief Destroy a stack handle.
 *
 * This function destroys a stack handle. \n
 * Because stack values can be memory-allocated data, callback function \n
 * for each stack data destruction is also provided.
 *
 * @param phStack  a stack handle to be destroyed.
 * @param fnDestroyCallback callback function for destroying internal stack values.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPStack_Destroy(IN OUT cap_handle *phStack, IN CbFnCAPStack fnDestroyCallback, IN void *pUserData);

#ifdef __cplusplus
}
#endif

#endif /* CAPSTACK_H_ */
