/*
 * CAPSocket.h
 *
 *  Created on: 2015. 8. 19.
 *      Author: chjej202
 */

#ifndef CAPSOCKET_H_
#define CAPSOCKET_H_

#include <cap_common.h>
#include <CAPString.h>

#ifdef __cplusplus
extern "C"
{
#endif

typedef enum _ESocketType
{
    SOCKET_TYPE_UDS, //!< Unix domain socket.
    SOCKET_TYPE_TCP, //!< TCP/IP Socket
} ESocketType;

typedef struct _SSocketInfo
{
    ESocketType enSocketType; //!< Socket type.
    cap_string strSocketPath; //!< Socket file path (Ex. /tmp/unixsocket for @ref SOCKET_TYPE_UDS, 127.0.0.1 for SOCKET_TYPE_TCP).
    int nPort; //!< Port number used by SOCKET_TYPE_TCP.
}SSocketInfo;


/** 
 * @brief Create a socket handle.
 *  
 * This function creates a socket handle which allows to communicate with other processes. \n
 * To use socket as a server, @a bIsServer needs to be TRUE. Otherwise, @a bIsServer needs to be FALSE.
 * 
 * @param pstSocketInfo a socket setting information.
 * @param bIsServer a socket as a server or client.
 * @param phSocket [out] a socket handle to be created.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_PARAM, @ref ERR_CAP_OUT_OF_MEMORY, \n
 *         @ref ERR_CAP_NOT_SUPPORTED.
 */
cap_result CAPSocket_Create(IN SSocketInfo *pstSocketInfo, IN cap_bool bIsServer, OUT cap_handle *phSocket);


/** 
 * @brief Destroy a socket handle.
 *  
 * This function closes a socket and destorys a socket handle.
 * 
 * @param phSocket a socket handle to be destroyed.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM.
 */
cap_result CAPSocket_Destroy(IN OUT cap_handle *phSocket);


/** 
 * @brief Bind a socket (server-only).
 *  
 * This function binds a socket. This is a server-only function.
 *
 * @warning this function needs to be called before @ref CAPSocket_Listen and @ref CAPSocket_Accept.
 * 
 * @param hServerSocket a socket handle to be binded.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_SOCKET_ERROR, @ref ERR_CAP_BIND_ERROR. \n
 *         @ref ERR_CAP_SOCKET_ERROR can be occurred when the socket operations are failed. \n
 *         @ref ERR_CAP_BIND_ERROR can be occurred when other process is using port/file.
 */
cap_result CAPSocket_Bind(cap_handle hServerSocket);


/** 
 * @brief Listen a socket (server-only).
 *  
 * This function listens a socket. This is a server-only function. \n
 * After calling this function, a server can receive multiple requests with @ref CAPSocket_Accept.
 *
 * @warning this function needs to be called before @ref CAPSocket_Accept.
 * 
 * @param hServerSocket a socket handle to listen.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_LISTEN_ERROR. \n
 *         @ref ERR_CAP_LISTEN_ERROR can be occurred when the listen operation is failed.
 */
cap_result CAPSocket_Listen(cap_handle hServerSocket);


/** 
 * @brief Accept a client connection (server-only).
 *  
 * This function accepts a client connection from different process/system. \n
 * To communicate with client, retrieved @a hSocket is used.  \n
 * To get new client connection, @a hSocket needs to be created as a client socket before. \n
 * SSocketInfo is not needed to be set for @a hSocket creation.
 * 
 * @param hServerSocket a socket handle to accept client connection.
 * @param nTimeout a maximum time to wait for client connection.
 * @param hSocket a retrieved client socket.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_INVALID_SOCKET, @ref ERR_CAP_ACCEPT_ERROR. \n
 *         If time is exceeded, @ref ERR_CAP_NET_TIMEOUT is retrieved.
 */
cap_result CAPSocket_Accept(cap_handle hServerSocket, IN int nTimeout, IN OUT cap_handle hSocket);


/** 
 * @brief Connect to a server (client-only).
 *  
 * This function connects to a server.
 * 
 * @param hClientSocket a socket handle.
 * @param nTimeout a maximum time to wait for connection.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_SOCKET_ERROR, @ref ERR_CAP_CONNECT_ERROR. \n
 *         If time is exceeded, @ref ERR_CAP_NET_TIMEOUT is retrieved.
 */
cap_result CAPSocket_Connect(cap_handle hClientSocket, IN int nTimeout);


/** 
 * @brief Send data (client-only). 
 *  
 * This function sends data.
 * 
 * @param hSocket a socket handle.
 * @param nTimeout a maximum time to wait for sending data.
 * @param pData data to send.
 * @param nDataLen the amount of data to send.
 * @param pnSentSize [out] the amount of data sent.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NET_SEND_ERROR. \n
 *         If time is exceeded, @ref ERR_CAP_NET_TIMEOUT is retrieved.
 */
cap_result CAPSocket_Send(cap_handle hSocket, IN int nTimeout, IN char *pData, IN int nDataLen, OUT int *pnSentSize);


/** 
 * @brief Receive data (client-only). 
 *  
 * This function receives data.
 * 
 * @param hSocket a socket handle.
 * @param nTimeout a maximum time to wait for receiving data.
 * @param pBuffer a buffer to receive data.
 * @param nBufferLen the size of buffer
 * @param pnReceivedSize [out] the amount of data received.
 *
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *         Errors to be returned - @ref ERR_CAP_INVALID_HANDLE, @ref ERR_CAP_INVALID_PARAM, \n
 *         @ref ERR_CAP_NET_RECEIVE_ERROR. \n
 *         If time is exceeded, @ref ERR_CAP_NET_TIMEOUT is retrieved.
 */
cap_result CAPSocket_Receive(cap_handle hSocket, IN int nTimeout, IN OUT char *pBuffer, IN int nBufferLen, OUT int *pnReceivedSize);


/**
 * @brief Print info
 * 
 * This function prints info
 * 
 * @param hSocket a socket handle.
 * 
 * @return @ref ERR_CAP_NOERROR is returned if there is no error. \n
 *          Errors to be returned - @ref ERR_CAP_INVALIED_HANDLE
 */
cap_result CAPSocket_PrintInfo(cap_handle hSocket);

#ifdef __cplusplus
}
#endif

#endif /* CAPSOCKET_H_ */
