import socket
import sys
import json

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 pingcli.py <server_host> <server_port>")
        sys.exit(1)

    server_host = sys.argv[1]
    try:
        server_port = int(sys.argv[2])
    except ValueError:
        print("client side error")
        sys.exit(1)

    server_address = (server_host, server_port)

    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        # Ask for username
        print("To Connect Please Enter 'join' followed by your name: ")
        print("or 'quit' to exit:")
        join_command = input()

        if join_command == "quit":
            print("Connection closed")
            sys.exit(1)
        elif join_command.startswith("join"):
            #the join command and the data is the username
            join_data = json.dumps({"command": "join", "data": join_command[5:]}).encode()
            sock.connect(server_address)
            sock.sendall(join_data)
            print("Connected to server")
        else:
            print("Invalid command")
            sys.exit(1)



        # Connect to server
        #sock.connect(server_address)
        
        while True:
            command = input("Enter command (or 'quit' to exit): ")

            if command == "quit":
                quit_message = json.dumps({"command": "quit", "data": "User has disconnected"}).encode()
                sock.sendall(quit_message)
                print("Connection closed")
                break
            elif command == "list":
                list_message = json.dumps({"command": "list", "data": "empty"}).encode()
                sock.sendall(list_message)
    
                # Receive the response from the server
                data = sock.recv(4096)  # Adjust buffer size as needed
                if not data:
                    print("No data received. Server may have closed the connection.")
                    break
                try:
                    connections_list = json.loads(data.decode())  # Decode and parse the JSON string
                    print("Current connections:", connections_list)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON from server: {e}")

            elif command == "join":
                print("You are already connected")
                continue
            
                    
            # Prompt the user to enter a message
            message = input("Enter message: ")

            # Create a dictionary with the user's command and message
            testdata = {"command": command, "data": message}

            # Convert the dictionary to a JSON string and then encode it to bytes
            encodedtestdata = json.dumps(testdata).encode()

            # Send the encoded data over the socket
            sock.sendall(encodedtestdata)
            
            # Assuming the server will always send a response for each message
            #data = sock.recv(1024)
            #print(f"Received from {server_address}: {data.decode()}")
            
    finally:
        sock.close()

if __name__ == "__main__":
    main()
