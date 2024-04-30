# Contributors: Jordan Dawson, Kevin Esquivel, Katrina Yu
# Course: CSC138-04
# Due Date: 04/30/2024
# Description: Implementation for a chatroom server that supports up to 10 users using TCP sockets.
#                Creates a thread for each user. 
# Usage: python3 server.py <port>

import socket
import sys
import json
import threading

lock = threading.Lock()

live_connections = {} # Indexed by addresses, stores usernames
live_addresses = set() # Set of all active addresses
client_connections = {} # Indexed by addresses, stores the corresponding socket

# Creates and sends list of active users to client
def senduserlist(connection):
        try:
            user_list = list(live_connections.values())     # Getting the list of usernames
            connection.send(json.dumps(user_list).encode()) # Sending to the user who requested it
        except:
            data = {"command": "excp", "data": "Server Error: Try Again.", "sender": None}
            connection.sendall(json.dumps(data).encode())
    
# Sends message to all active users except for the sender
def broadcast(json_command, json_data, client_address):
    with lock: # Not client specific
        data = {} # Data is based on client or server broadcast
        if client_address: # Client broadcasts
            # Adding BCST to beginning of message to show it's not a direct message
            json_data = "BCST " + json_data 
            data = {"command": json_command,"data": json_data, "sender": live_connections[client_address]}
        else: # Sever broadcasts when there is no client
            data = {"command": json_command,"data": json_data, "sender": None}
        
        encoded_data = json.dumps(data).encode()
        for client in live_addresses: # Sending the data to all the addresses except sender
            if client != client_address:
                client_connections[client].send(encoded_data)

# Jordan Dawson - mesg takes the command, uses the end of that to find the recipient, 
# then sends the message in form of the data, as well as the senders handle to the recipient.
def mesg(json_command, json_data, client_address):
    with lock: 
        sent = 0       
        for client in live_addresses:
            if live_connections[client] == json_data[0]:
                data = {"command": json_command, "data": json_data[1], "sender": live_connections[client_address]}
                encoded_data = json.dumps(data).encode()
                client_connections[client].send(encoded_data)
                sent += 1
        if sent != 1:
            data = {"command": "excp", "data": "Unknown Recipient", "sender": None}
            client_connections[client_address].sendall(json.dumps(data).encode())

# Inside thread for each client handle requests and responses
def handle_client(connection, client_address):
    try:
        # Initial data reception to add client to live_connections
        rec_data = connection.recv(2048)
        decoded_json = json.loads(rec_data.decode('utf-8'))
        #TODO: print(f"Initial data from {client_address}: {decoded_json['data']}")
        print(f"{decoded_json['data']} joined the chat room.")
        live_connections[client_address] = decoded_json["data"]

        # Server broadcast for user joining
        connection.sendall(json.dumps("connected").encode())
        broadcast("bcst", f"{live_connections[client_address]} has joined the chat room.", None)

        # Continuous handling of client requests
        while True:
            message = connection.recv(2048)
            if not message:
                break  # Client has disconnected

            decoded_json = json.loads(message.decode('utf-8'))
            json_command = decoded_json["command"]
            json_data = decoded_json["data"]

            if json_command == "list":
                senduserlist(connection)
                
            elif json_command == "mesg":
                try:
                    split_json_data = json_data.split(" ", 1)
                    mesg(json_command, split_json_data, client_address)
                except:
                    data = {"command": "except", "data": "Usage:mesg <username> <message>"}
                    connection.sendall(json.dumps(data).encode())

            elif json_command == "bcst":
                broadcast(json_command, json_data, client_address) 

            elif json_command == "quit":
                broadcast("bcst", f"{live_connections[client_address]} has left the chat room.", None)
                print(f"{client_address} has disconnected")
                break
            
            # Logging for server data
            '''if json_data != "empty":
                print(f"{client_address}: {json_data}")
                response = f"RECEIVED : {json_data}"
                connection.sendall(response.encode())'''

    finally:
        # Deregistering client after they quit
        with lock:
            if client_address in live_connections:
                del live_connections[client_address]  # Remove client from live_connections
            live_addresses.remove(client_address) # Remove client address from live_addresses
            client_connections.pop(client_address)
            connection.close()

def start_server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', port))
    serverSocket.listen(10)
    print('Chat Server Started')
    print('Server is running on port: ', port)

    try:
        while True:
            connection, client_address = serverSocket.accept()
            #TODO print(f'Connection incoming from {client_address}')
            if len(live_addresses) <= 9: # Can only join if there are nine or less users currently on the server
                # Registering the client
                live_addresses.add(client_address)
                client_connections[client_address] = connection

                # Create a new thread for each connected client
                client_thread = threading.Thread(target=handle_client, args=(connection, client_address))
                client_thread.start()
                print(f'Connected with {client_address}')
            else:
                print(f"Too many users on the server, disconnecting {client_address}")
                # Close the connection
                connection.close()

    # ^C to close server
    except KeyboardInterrupt:
        # Broadcast to all clients to shutdown
        broadcast("bcst", "Server is shutting down.", None)
        print("\nServer is shutting down.")
    finally:
        serverSocket.close()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 server.py <port>")
        sys.exit(1)

    try:
        port = int(sys.argv[1])
        start_server(port)
    except ValueError:
        print("Server side error: Please provide a valid port number.")
        sys.exit(1)
