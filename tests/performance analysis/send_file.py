import socket

FORMAT = "utf-8"
SIZE = 1024

def send(s):
    client = s
    
    #opening and reading the file data
    file = open("test.txt", "r")
    data = file.read()
    
    #Sending the filename to the server
    client.send("test.txt".encode(FORMAT))
    
    #sending the file data to the server
    client.send(data.encode(FORMAT))
    
    #closing the file
    file.close()
    
    #closing the connection from the server
    client.close()


if __name__ == "__main__":
    main()