import os
import sys
import time
import json
import socket
import pickle
import pathlib
import datetime
import platform
import http.client


def download_file(host, port, path, filename):
    conn = http.client.HTTPConnection(host, port)
    conn.request('GET', path)
    response = conn.getresponse()
    
    if response.status == 200:
        with open(filename + " received at " + str(datetime.datetime.now()).replace(":", "---"), 'wb') as file:
            file.write(response.read())
        print('Datei erfolgreich heruntergeladen.')
    else:
        print(f'Fehler beim Herunterladen der Datei: {response.status} {response.reason}')
    
    conn.close()

def start_client(host, port):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f'Verbunden mit dem Server an {host}:{port}')
    
    # Daten vom Server empfangen
    received_data = client_socket.recv(256) # mehr als genug
    
    # Deserialisieren der empfangenen Daten
    data = pickle.loads(received_data)
    print(f'Daten empfangen: {data}')
    print("Datei: " + data["file"])
    
    client_socket.close()

    time.sleep(1)
    download_file("localhost", 65432, data["file"], "testfile.blend")

def register():
    return

def loop():
    stop = False
    while not stop:
        inp = input("> ")
        if (inp.lower() == "register"):
            register()

def main():
    start_client('localhost', 65432)
    return
    blenderPath = ""
    blenderArgs = ""
    serverAddress = ""
    autoRegister = False

    if not (os.path.exists("config.json")):
        print("No config file found")
    else:
        with open("config.json") as file:
            try:
                config = json.load(file)
                if "blenderPath" in config:
                    blenderPath = config["blenderPath"]
                if "blenderArgs" in config:
                    blenderArgs = config["blenderArgs"]
            except Exception as ex:
                cwd = pathlib.Path().resolve()
                print("Failed to parse " +  os.path.join(cwd, "config.json"))
                print("Exception: " + str(ex))


    args = sys.argv
    print(args)
    for i in range(1, len(args)):
        if (args[i].lower() == "-h" or "-help"):
            print("Available command line arguments:")

        elif (args[i].lower() == "-ar" or "-autoregister"):
            autoRegister = True

        elif (args[i].lower() == "-s" or "-server"):
            i += 1
            if (i == len(args)):    
                print("No server address specified after " + str(args[i - 1]))
                return
            
            serverAddress = args[i]
            #TODO(maybe): check for address validity


        elif (args[i].lower() == "-b" or "-blender" or "-blenderpath"):
            i += 1
            if (i == len(args)):    
                print("No blender path specified after "  + str(args[i - 1]))
                return
            
            blenderPath = args[i]
            if os.name == "nt":
                if os.path.isdir(blenderPath):
                    blenderPath = os.path.join(blenderPath, "blender.exe")
                
                #else if isfile(blenderPath):
                elif not blenderPath.endswith(".exe"):
                    print("The file which was passed as Blender path is no executable")
                    return
                    
                if not os.path.exists(blenderPath):
                    print("Coulnd't find " + blenderPath)
                    return
                    
            elif os.name == "posix":
                if os.path.isdir(blenderPath):
                    if (platform.system() == "Darwin"):
                        blenderPath = os.path.join(blenderPath, "Contents/MacOs/Blender")
                    elif (platform.system() == "Linux"):
                        blenderPath = os.path.join(blenderPath, "blender")
                    else:
                        print("Unknown operating system: " + platform.system())

                if not os.path.exists(blenderPath):
                    print("Coulnd't find " + blenderPath)
                    return
                
                if not os.access(blenderPath, os.X_OK):
                    print("Not executable: " + blenderPath)
                    return
                    #TODO: Test if <blenderPath> is definitely an executable program

            else: # java (?)
                print("Unsupported platform: " + os.name)

    
    if (autoRegister):
        register()
    else:
        loop()

main()