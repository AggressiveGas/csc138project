# Contributors: Jordan Dawson, Kevin Esquivel, Katrina Yu
# Course: CSC138-04
# Due Date: 04/30/2024
# Description: Implementation for a chatroom client using a TCP socket to
#               connect with the server.
# Usage: python3 pingcli.py <server_host> <server_port>

import select
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
        print("Client side error")
        sys.exit(1)

    server_address = (server_host, server_port)

    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        next = True
        while next:
            # Socket list to switch between receiving data from the server and the user
            sockets = [sys.stdin, sock]
            read, write, error = select.select(sockets,[],[])

            for socks in read:
                if socks == sock:
                    # Ask for username
                    print("To Connect Please Enter 'join' followed by your name: ")
                    print("or 'quit' to exit:")
                    join_command = input() # Non case sensitive commands
                    split_command = join_command.lower().split()
                    username = ""
                    if split_command[0] == "quit":
                        print("Connection closed")
                        sys.exit(1)
                    elif split_command[0] == "join":
                        # The join command and data = username
                        join_data = json.dumps({"command": "join", "data": join_command[5:]}).encode()
                        username = join_command[5:]
                        try:
                            sock.connect(server_address)
                            try:
                                sock.sendall(join_data)
                                sock.settimeout(1)
                                sock.recv(4096)
                                print("Connected to server")
                                # Displaying commands and their usage to the user
                                print('\n"list"   for a list of users in the chat room')
                                print('"mesg <username> <message>"  to directly message another user')
                                print('"bcst <message>" to send a message to the chat room')
                                print('"quit"   to leave the chat room\n')
                                next = False
                            except:
                                print("Too many users. Please try again later.")
                                sys.exit(1)
                        except:
                            # No reponse from server
                            print("Server is not available")
                            sys.exit(1)
                    else:
                        print("Invalid command")
                        sys.exit(1)

        
        while True:
            # Socket list to switch between receiving data from the server and the user
            socket_list = [sys.stdin, sock]
            read_sockets, write_socket, error_socket = select.select(socket_list,[],[])

            for socks in read_sockets:
                if socks == sock:
                    try: 
                        # Continuously receviving data from the server   
                        data = sock.recv(4096)

                        if not data:
                            break
                        
                        decoded_json = json.loads(data.decode())
                        json_data = decoded_json["data"]
                        json_sender = decoded_json["sender"]

                        if json_sender == None:
                            print(f"{json_data}")
                            if json_data == "Server is shutting down.":
                                print("Connection closed")
                                sock.close()
                                sys.exit(1)

                        else:
                            # Displaying broadcast and direct messages to client
                            print(f"{json_sender}: {json_data}")
                    except:
                        continue
                else:
                    user_input = input() # Receiving data from the user
                    command = user_input.lower().split() # removing case sensitivity

                    # Sends message to broadcast user leaving chat room to server and closes client
                    if command[0] == "quit":
                        quit_message = json.dumps({"command": "quit", "data": "User has disconnected"}).encode()
                        sock.sendall(quit_message)
                        print("Connection closed")
                        sock.close()
                        sys.exit(1)

                    # Sends back list of active users in the chat room
                    elif command[0] == "list" and len(command) == 1:
                        list_message = json.dumps({"command": "list", "data": "empty"}).encode()
                        sock.sendall(list_message)
            
                        # Receive the response from the server
                        data = sock.recv(4096)  # Adjust buffer size as needed
                        if not data:
                            print("No data received. Server may have closed the connection.")
                            break
                        try:
                            connections_list = json.loads(data.decode())  # Decode and parse the JSON string
                            
                            # Formatting list of users to display
                            # Format: name1, name2, name3, etc
                            list_str = str(connections_list)
                            formatted_str = (list_str[1:len(list_str)-1]).replace("'", "")
                            print(f"Current connections: {formatted_str}") 
                        except json.JSONDecodeError as e:
                            print(f"Error decoding JSON from server: {e}")
                    
                    # Send feedback for trying to join again
                    elif command[0] == "join":
                        print("You are already connected to the chat room.")
                        continue
                    
                    # Direct messaging another user, send data to server
                    elif command[0] == "mesg":
                        # Create a dictionary with the user's command, data: username & message
                        data = {"command": "mesg", "data": user_input[5:]}

                        # Convert the dictionary to a JSON string and then encode it to bytes
                        encodeddata = json.dumps(data).encode()

                        # Send the encoded data over the socket
                        sock.sendall(encodeddata)
                    
                    # Broadcasting to chat room, send data to server
                    elif command[0] == "bcst":
                        # Dictionary entry for broadcast message
                        bcstdata = {"command": "bcst", "data": user_input[5:]}
                        # Converting the dictionary to a JSON string for the broadcast and encoding into bytes
                        endcodedbcst = json.dumps(bcstdata).encode()
                        sock.sendall(endcodedbcst)
                        
                        # Feedback for user
                        print(f"{username} is sending a broadcast.")
                    else:
                        print("Invalild command.")
            
    finally:
        sock.close()
        sys.exit(1)

if __name__ == "__main__":
    main()
