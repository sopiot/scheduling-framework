#ifndef _SOCKETPROTOCOLHANDLER_H_
#define _SOCKETPROTOCOLHANDLER_H_

#include <sop_common.h>

#ifdef __cplusplus
extern "C" {
#endif

cap_result SocketProtocol_ReceivePacket(cap_handle hSocketForResponse,
                                        char **ppszPacketData,
                                        int *nPacketData);
cap_result SocketProtocol_SendPacket(cap_handle hSocketForRequest,
                                     cap_handle hLockForSocketForRequest,
                                     char *pszPayload, int nPayloadLen);
#ifdef __cplusplus
}
#endif

#endif /* _SOCKETPROTOCOLHANDLER_H_ */
