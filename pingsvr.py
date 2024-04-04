import socket
import sys
import json
import threading

lock = threading.Lock()


live_connections = {}

def senduserlist(connection):
        # Before serialization, convert the keys to strings if they are tuples
        #live_connections_str_keys = {str(key): value for key, value in live_connections.items()}

        #response = json.dumps(live_connections_str_keys)
        #connection.sendall(response.encode())
    
    ###
        with lock:
            user_list = list(live_connections.values())
            connection.sendall(json.dumps(user_list).encode())
    


def handle_client(connection, clientAddress, live_connections):
    try:
        with lock:
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
                


            #elif json_command == "mesg":
                

            elif json_command == "quit":
                print(f"{clientAddress} has disconnected")
                break

            print(f"{clientAddress}: {json_data}")
            response = "RECEIVED : " + json_data
            connection.sendall(response.encode())

    finally:
        with lock:
            if clientAddress in live_connections:
                del live_connections[clientAddress]  # Remove client from live_connections
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

            # Create a new thread for each connected client
            client_thread = threading.Thread(target=handle_client, args=(connection, clientAddress, live_connections))
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
