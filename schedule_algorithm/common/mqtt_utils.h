#ifndef MQTT_UTILS_H_
#define MQTT_UTILS_H_

#include "CAPString.h"
#include "sop_common.h"

#ifdef __cplusplus
extern "C" {
#endif

/**
 * @brief Retrieve a item(identifier) *char pointer* from a topic list by
 * offset. \n
 * [Notice] ppszItem should be freed after use.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param nOffset offset to select an item
 * @param ppszItem [out] char pointer of the selected item.
 * @param pnItemLen [out] length of the selected item.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetItemFromTopicList_Char(IN cap_handle hTopicItemList, IN int nOffset, OUT char **ppszItem,
                                     OUT int *pnItemLen);

/**
 * @brief Retrieve a item(identifier) *cap_string* from a topic list by offset.
 * \n [Notice] pstrItem should not be freed because it just points the topic
 * list item.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param nOffset offset to select an item
 * @param pstrLastItem [out] cap_string of the selected item.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetItemFromTopicList_Str(IN cap_handle hTopicItemList, IN int nOffset, OUT cap_string *pstrItem);

/**
 * @brief Retrieve the last item(identifier) *char pointer* from a topic list.
 *
 * [Notice] ppszLastItem should be freed after use.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param ppszLastItem [out] char pointer of the last item.
 * @param pnLastItemLen [out] length of the last item.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetLastItemFromTopicList_Char(IN cap_handle hTopicItemList, OUT char **ppszLastItem, OUT int *pnLastItemLen);

/**
 * @brief Retrieve the last item(identifier) *cap_string* from a topic list. \n
 * [Notice] pstrLastItem should not be freed because it just points the topic
 * list item.
 *
 * @param hTopicItemList a linked list that contains topic strings.
 * @param pstrLastItem [out] cap_string of the last item.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned -
 *          @ref ERR_CAP_INVALID_PARAM,
 *          @ref ERR_CAP_OUT_OF_MEMORY.
 */
cap_result GetLastItemFromTopicList_Str(IN cap_handle hTopicItemList, OUT cap_string *pstrLastItem);

#ifdef __cplusplus
}
#endif

#endif  // MQTT_UTILS_H_
