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


def download_file(address, path, filename): #host, port, path, filename
    conn = http.client.HTTPConnection(address["host"], address["port"]) #(host, port)
    conn.request('GET', path)
    response = conn.getresponse()
    
    if response.status == 200:
        with open(filename + " received at " + str(datetime.datetime.now()).replace(":", "---"), 'wb') as file:
            file.write(response.read())
        print('Datei erfolgreich heruntergeladen.')
    else:
        print(f'Fehler beim Herunterladen der Datei: {response.status} {response.reason}')
    
    conn.close()

def start_client(address, httpAddress): #(host, port)
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect(address) #((host, port))
    print(f'Verbunden mit dem Server an ' + address)
    
    # Daten vom Server empfangen
    received_data = client_socket.recv(256) # mehr als genug
    
    # Deserialisieren der empfangenen Daten
    data = pickle.loads(received_data)
    print(f'Daten empfangen: {data}')
    print("Datei: " + data["file"])
    
    client_socket.close()

    time.sleep(1)
    download_file(httpAddress, data["file"], "testfile.blend")

def register():
    return

def loop():
    stop = False
    while not stop:
        inp = input("> ")
        if (inp.lower() == "register"):
            register()

def checkBlenderPath(blenderPath: str):
    if os.name == "nt":
        if os.path.isdir(blenderPath):
            blenderPath = os.path.join(blenderPath, "blender.exe")
        
        #else if isfile(blenderPath):
        elif not blenderPath.endswith(".exe"):
            print("The file which was passed as Blender path is no executable")
            exit()
            
        if not os.path.exists(blenderPath):
            print("Coulnd't find " + blenderPath)
            exit()
            
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
            exit()
        
        if not os.access(blenderPath, os.X_OK):
            print("Not executable: " + blenderPath)
            exit()
            #TODO: Test if <blenderPath> is definitely an executable progra
    else: # java (?)
        print("Unsupported platform: " + os.name)
        exit()
    
    return blenderPath

def getArgValue(message: str, args: list[str], index: int):
    if (index == len(args)):    
        print("No " + message + " specified after "  + str(args[index- 1]))
        exit()
    
    return args[index]

def main():
    start_client("localhost:65432", {"host": "localhost", "port": 65432})
    return
    # make these variables global / wrap into singleton object / use config dictionary ???
    blenderPath = ""
    blenderArgs = ""
    serverAddress = "" #TODO:set default value
    httpHost = "" #TODO:set default value
    httpPort = -1 #TODO:set default value
    autoRegister = False
    dumpConfig = False

    #TODO:outsource to function
    if not (os.path.exists("config.json")):
        print("No config file found")
    else:
        with open("config.json") as file:
            try:
                config = json.load(file)
                if "blenderPath" in config:
                    blenderPath = config["blenderPath"]
                    blenderPath = checkBlenderPath(blenderPath)
                    if (blenderPath == ""):
                        return
                    
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

        elif (args[i].lower() == "-d" or "-dump" or "-dc" or "-dumpconfig"):
            dumpConfig = True

        elif (args[i].lower() == "-ar" or "-autoregister"):
            autoRegister = True

        elif (args[i].lower() == "-s" or "-server"):
            i += 1            
            serverAddress = getArgValue("server address", args, i)
            #TODO(maybe): check for address validity

        elif (args[i].lower() == "-httphost"):
            i += 1
            httpHost = getArgValue("HTTP host", args, i)

        elif (args[i].lower() == "-httpport"):
            i += 1
            port = getArgValue("HTTP port", args, i)
            try:
                httpPort = int(host)

            except:
                print("Failed to parse HTTP port to integer: " + port)
                returns

        elif (args[i].lower() == "-b" or "-blender" or "-blenderpath"):
            i += 1
            blenderPath = getArgValue("blender path", args, i)
            blenderPath = checkBlenderPath(blenderPath)
    
    #TODO:outsource to function
    if (dumpConfig):
        config = {
            "blenderPath": blenderPath,
            "blenderArgs": blenderArgs,
            "serverAddress": serverAddress,
            "autoRegister": autoRegister,
            "httpHost": httpHost,
            "httpPort": httpPort
        }

        try:
            with open("config.json", "w") as file:
                json.dump(config, file)

        except Exception as ex:
            print("Failed to write to config.json")
            print("Exception: " + ex)

    
    if (autoRegister):
        register()
    else:
        loop()

main()