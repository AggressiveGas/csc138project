import socket
import sys
import json
import threading

lock = threading.Lock()

live_connections = {}
live_addresses = set()
client_connections = {}

def senduserlist(connection):
        user_list = list(live_connections.values())     # Getting the list of usernames
        connection.send(json.dumps(user_list).encode()) # Sending to the user who requested it
    
def broadcast(json_command, json_data, clientAddress):
    with lock: # Not client specific
        for client in live_addresses: # Sending the data to all the addresses except sender
            if client != clientAddress:
                json_data = "BCST " + json_data # Adding BCST to beginning of message to show it's not a direct message
                data = {"command": json_command,"data": json_data, "sender": live_connections[clientAddress]}
                encoded_data = json.dumps(data).encode()
                client_connections[client].send(encoded_data)

#Jordan Dawson - mesg takes the command, uses the end of that to find the recipient, then sends the message in form of the data,
#as well as the senders handle to the recipient.
def mesg(json_command, json_data, clientAddress):
    with lock: 
        sent = 0       
        for client in live_addresses:
            print(f"{json_data[0]} and {json_data[1]}")
            if live_connections[client] == json_data[0]:
                data = {"command": json_command, "data": json_data[1], "sender": live_connections[clientAddress]}
                encoded_data = json.dumps(data).encode()
                client_connections[client].send(encoded_data)
                sent += 1
        if sent != 1:
            data = {"command": "except", "data": "Unknown Recipient"}
            client_connections[clientAddress].sendall(json.dumps(data).encode())

def handle_client(connection, clientAddress):
    try:
        # Initial data reception to add client to live_connections
        rec_data = connection.recv(2048)
        decoded_json = json.loads(rec_data.decode('utf-8'))
        print(f"Initial data from {clientAddress}: {decoded_json['data']}")
        live_connections[clientAddress] = decoded_json["data"]

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
                    print(f"json data: {split_json_data}")
                    mesg(json_command, split_json_data, clientAddress)
                except:
                    data = {"command": "except", "data": "Usage:mesg <username> <message>"}
                    connection.sendall(json.dumps(data).encode())

            elif json_command == "bcst":
                broadcast(json_command, json_data, clientAddress)
                

            elif json_command == "quit":
                print(f"{clientAddress} has disconnected")
                break

            print(f"{clientAddress}: {json_data}")
            response = f"RECEIVED : {json_data}"
            connection.sendall(response.encode())


    finally:
        with lock:
            if clientAddress in live_connections:
                del live_connections[clientAddress]  # Remove client from live_connections
            live_addresses.remove(clientAddress) # Remove client address from live_addresses
            client_connections.pop(clientAddress)
            connection.close()

def start_server(port):
    serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serverSocket.bind(('0.0.0.0', port))
    serverSocket.listen(10)
    print('Server is running on port', port)

    try:
        while True:
            connection, clientAddress = serverSocket.accept()
            print(f'Connection from {clientAddress}')

            live_addresses.add(clientAddress)
            client_connections[clientAddress] = connection

            # Create a new thread for each connected client
            client_thread = threading.Thread(target=handle_client, args=(connection, clientAddress))
            client_thread.start()

    except KeyboardInterrupt:
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
