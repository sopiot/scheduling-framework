#include "mqtt_utils.h"

#include "CAPLinkedList.h"
#include "CAPThread.h"

cap_result GetItemFromTopicList_Char(IN cap_handle hTopicItemList,
                                     IN int nOffset, OUT char **ppszItem,
                                     OUT int *pnItemLen) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strItem = NULL;
  int nStringLen = 0;
  char *pszTemp = NULL;
  char *pszItem = NULL;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(ppszItem, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(pnItemLen, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST, nOffset,
                             (void **)&strItem);
  ERRIFGOTO(result, _EXIT);

  nStringLen = CAPString_Length(strItem);

  pszItem = malloc((nStringLen + 1) * sizeof(char));
  ERRMEMGOTO(pszItem, result, _EXIT);

  pszTemp = CAPString_LowPtr(strItem, NULL);
  ERRMEMGOTO(pszTemp, result, _EXIT);

  memcpy(pszItem, pszTemp, sizeof(char) * nStringLen);
  pszItem[nStringLen] = '\0';

  *ppszItem = pszItem;
  *pnItemLen = nStringLen + 1;

  result = ERR_CAP_NOERROR;
_EXIT:
  if (result != ERR_CAP_NOERROR) {
    SAFEMEMFREE(pszItem);
  }
  return result;
}

cap_result GetItemFromTopicList_Str(IN cap_handle hTopicItemList,
                                    IN int nOffset, OUT cap_string *pstrItem) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strItem = NULL;
  int nStringLen = 0;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(pstrItem, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_FIRST, nOffset,
                             (void **)&strItem);
  ERRIFGOTO(result, _EXIT);

  *pstrItem = strItem;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}

cap_result GetLastItemFromTopicList_Char(IN cap_handle hTopicItemList,
                                         OUT char **ppszLastItem,
                                         OUT int *pnLastItemLen) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strLastItem = NULL;
  int nStringLen = 0;
  char *pszTemp = NULL;
  char *pszLastItem = NULL;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(ppszLastItem, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);
  IFVARERRASSIGNGOTO(pnLastItemLen, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_LAST, -1,
                             (void **)&strLastItem);
  ERRIFGOTO(result, _EXIT);

  nStringLen = CAPString_Length(strLastItem);

  if (nStringLen == 0) {
    return ERR_CAP_NULL_FROM_LIST;
  }

  pszLastItem = malloc((nStringLen + 1) * sizeof(char));
  ERRMEMGOTO(pszLastItem, result, _EXIT);

  pszTemp = CAPString_LowPtr(strLastItem, NULL);
  ERRMEMGOTO(pszTemp, result, _EXIT);

  memcpy(pszLastItem, pszTemp, sizeof(char) * nStringLen);
  pszLastItem[nStringLen] = '\0';

  *ppszLastItem = pszLastItem;
  *pnLastItemLen = nStringLen + 1;

  result = ERR_CAP_NOERROR;
_EXIT:
  if (result != ERR_CAP_NOERROR) {
    SAFEMEMFREE(pszLastItem);
  }
  return result;
}

cap_result GetLastItemFromTopicList_Str(IN cap_handle hTopicItemList,
                                        OUT cap_string *pstrLastItem) {
  cap_result result = ERR_CAP_UNKNOWN;
  cap_string strLastItem = NULL;

  IFVARERRASSIGNGOTO(hTopicItemList, NULL, result, ERR_CAP_INVALID_PARAM,
                     _EXIT);
  IFVARERRASSIGNGOTO(pstrLastItem, NULL, result, ERR_CAP_INVALID_PARAM, _EXIT);

  result = CAPLinkedList_Get(hTopicItemList, LINKED_LIST_OFFSET_LAST, -1,
                             (void **)&strLastItem);
  ERRIFGOTO(result, _EXIT);

  *pstrLastItem = strLastItem;

  result = ERR_CAP_NOERROR;
_EXIT:
  return result;
}