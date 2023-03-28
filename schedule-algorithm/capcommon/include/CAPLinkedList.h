#ifndef CAPLINKEDLIST_H_
#define CAPLINKEDLIST_H_

#include "cap_common.h"

#ifdef __cplusplus
extern "C"
{
#endif

typedef enum _ELinkedListOffset {
	LINKED_LIST_OFFSET_FIRST,
	LINKED_LIST_OFFSET_LAST,
	LINKED_LIST_OFFSET_CURRENT,
	LINKED_LIST_OFFSET_DEFAULT = LINKED_LIST_OFFSET_LAST,
} ELinkedListOffset;

typedef cap_result (*CbFnCAPLinkedList)(IN int nOffset, IN void *pData, IN void *pUserData);
typedef cap_result (*CbFnCAPLinkedListDup)(IN int nOffset, IN void *pDataSrc, IN void *pUserData, OUT void **ppDataDst);


/** 
 * @brief Create a linked list.
 *  
 * This function creates a linked list.
 *
 * @warning CAPLinkedList does not provide callback function for destroying internal data. \n
 * To destroy internal data, use @ref CAPLinkedList_Traverse or Use @ref CAPLinkedList_Get with for-loop. \n
 * Then, call @ref CAPLinkedList_Destroy to free the whole data structure.
 *
 * @param phLinkedList [out] a linked list handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result CAPLinkedList_Create(OUT cap_handle *phLinkedList);


/** 
 * @brief Add data into the linked list.
 *  
 * This function adds an item into the linked list. \n
 * By using @a enOffset and @a nIndex, data can be inserted any specific location. \n
 * Check @ref ELinkedListOffset for base offset setting. \n
 * 
 * To insert data at head:
 *
 *     @code{.c}
 *     CAPLinkedList_Add(hLinkedList, LINKED_LIST_OFFSET_FIRST, 0, pData);
 *     @endcode
 *  
 *
 * To insert data at tail:
 *
 *     @code{.c}
 *     CAPLinkedList_Add(hLinkedList, LINKED_LIST_OFFSET_LAST, 0, pData);
 *     @endcode
 *     
 * @param hLinkedList a linked list handle.
 * @param enOffset a base offset. @ref ELinkedListOffset.
 * @param nIndex an index from the base offset.
 * @param pData a data to add into the linked list.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Add(cap_handle hLinkedList, IN ELinkedListOffset enOffset, IN int nIndex, IN void *pData);


/** 
 * @brief Move the linked list offset.
 * 
 * This function moves the offset of @ref LINKED_LIST_OFFSET_CURRENT.
 *
 * @param hLinkedList a linked list handle.
 * @param enOffset a base offset. @ref ELinkedListOffset.
 * @param nIndex an index from the base offset.
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPLinkedList_Seek(cap_handle hLinkedList, IN ELinkedListOffset enOffset, IN int nIndex);


/** 
 * @brief Get data of specific node in linked list.
 *  
 * This function retrieves data in the linked list. \n
 * If @a enOffset and @a nIndex are used to specifiy the node in the linked list.
 *
 * @param hLinkedList a linked list handle.
 * @param enOffset a base offset. @ref ELinkedListOffset.
 * @param nIndex an index from the base offset.
 * @param ppData [out] a retrieved data.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPLinkedList_Get(cap_handle hLinkedList, IN ELinkedListOffset enOffset, IN int nIndex, OUT void **ppData);


/** 
 * @brief Change data of existing linked list node.
 *  
 * This function retrieves data in the linked list. \n
 * If @a enOffset and @a nIndex are used to specifiy the node in the linked list.
 *
 * @param hLinkedList a linked list handle.
 * @param enOffset a base offset. @ref ELinkedListOffset.
 * @param nIndex an index from the base offset.
 * @param pData a data to set.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPLinkedList_Set(cap_handle hLinkedList, IN ELinkedListOffset enOffset, IN int nIndex, IN void *pData);


/** 
 * @brief Get size of the linked list.
 *  
 * This function retrieves the number of nodes in the linked list.
 *
 * @param hLinkedList a linked list handle.
 * @param pnLength [out] the size of linked list.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_GetLength(cap_handle hLinkedList, OUT int *pnLength);


/** 
 * @brief Remove the specific node of the linked list.
 *  
 * This function removes the node specified by @a enOffset and @a nIndex.
 *
 * @warning This function does not remove internal data structure, \n
 * so internal data removal is needed before calling this function. \n
 * Use @ref CAPLinkedList_Get to get and free the data. Then, call this function.
 *
 * @param hLinkedList a linked list handle.
 * @param enOffset a base offset. @ref ELinkedListOffset.
 * @param nIndex an index from the base offset.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Remove(cap_handle hLinkedList, IN ELinkedListOffset enOffset, IN int nIndex);


/** 
 * @brief Remove all nodes of the linked list.
 *  
 * @warning This function does not remove internal data structure, \n
 * so internal data removal is needed before calling this function. \n
 * Use @ref CAPLinkedList_Get to get and free the data. Then, call this function.
 *
 * @param hLinkedList a linked list handle.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Clear(cap_handle hLinkedList);


/** 
 * @brief Traverse linked list data structure.
 *  
 * This function traverses all the nodes in the linked list. 
 *
 * @param hLinkedList a linked list handle.
 * @param fnCallback callback function for accessomg each linked list node.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Traverse(cap_handle hLinkedList, IN CbFnCAPLinkedList fnCallback, IN void *pUserData);


/** 
 * @brief Merge two linked lists.
 *  
 * This function attach @a phLinkedList_end to @a phLinkedList_front. \n
 * After performing this function, phLinkedList_end is removed and returns NULL. \n
 * front part of the linked list come from @a phLinkedList_front, \n
 * and the later part of the linked list come from @a phLinkedList_end.
 *
 * @param phLinkedList_front destination linked list.
 * @param phLinkedList_end source linked list to be merged into @a phLinkedList_front.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Attach(IN OUT cap_handle phLinkedList_front, IN cap_handle *phLinkedList_end);


/** 
 * @brief Duplicate a linked list.
 *  
 * This function copies all the data from @a hLinkedListSrc to @a hLinkedListDst. \n
 * To copy each internal linked list node, @a fnCallback callback function is used. \n
 * The destination linked list must not have any node and the source linked list must have \n
 * at least one node. Otherwise, it retrieves an error.
 *
 * @param hLinkedListDst a destination linked list handle.
 * @param hLinkedListSrc a source linked list handle.
 * @param fnCallback callback function for copying internal data of each linked list node.
 * @param pUserData user data pointer passing to the callback function.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_NOT_EMTPY, 
 *         @ref ERR_CAP_NO_DATA.
 */
cap_result CAPLinkedList_Duplicate(cap_handle hLinkedListDst, cap_handle hLinkedListSrc, IN CbFnCAPLinkedListDup fnCallback, IN void *pUserData);


/** 
 * @brief Not Implemented yet.
 *
 */
cap_result CAPLinkedList_Split(IN OUT cap_handle phLinkedList_front, IN OUT cap_handle phLinkedList_end);


/** 
 * @brief Destroy a linked list handle.
 *  
 * This function destroys a linked list handle.
 * 
 * @warning please read warning shown in @ref CAPLinkedList_Create.
 *
 * @param phLinkedList a linked list handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPLinkedList_Destroy(IN OUT cap_handle *phLinkedList);

#ifdef __cplusplus
}
#endif

#endif /* CAPLINKEDLIST_H_ */
