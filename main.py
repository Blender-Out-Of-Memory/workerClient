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
from types import SimpleNamespace

import WCConfig

CONFIG_JSON_PATH = "config.json"

config: WCConfig.WCConfig


def download_file(host, port, path, filename): #host, port, path, filename
    conn = http.client.HTTPConnection(host, port) #(host, port)
    conn.request('GET', path)
    response = conn.getresponse()
    
    if response.status == 200:
        with open(filename + " received at " + str(datetime.datetime.now()).replace(":", "---"), 'wb') as file:
            file.write(response.read())
        print('Datei erfolgreich heruntergeladen.')
    else:
        print(f'Fehler beim Herunterladen der Datei: {response.status} {response.reason}')
    
    conn.close()

def start_client(host: str, port: int):
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))
    print(f'Verbunden mit dem Server an ' + host + ":" + str(port))
    
    # Daten vom Server empfangen
    received_data = client_socket.recv(256) # mehr als genug
    
    # Deserialisieren der empfangenen Daten
    data = pickle.loads(received_data)
    print(f'Daten empfangen: {data}')
    print("Datei: " + data["file"])
    
    client_socket.close()

    time.sleep(1)
    download_file(host, port, data["file"], "testfile.blend")

def register():
    #Register at server as available worker
    #Start thread to listen to tasks
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

def parseArgs(args: list[str]):
    global config
    dumpConfig: bool = False

    for i in range(1, len(args)):
        if (args[i].lower() == "-h" or "-help"):
            print("Available command line arguments:")

        elif (args[i].lower() == "-d" or "-dump" or "-dc" or "-dumpconfig"):
            dumpConfig = True

        elif (args[i].lower() == "-ar" or "-autoregister"):
            config.autoRegister = True

        elif (args[i].lower() == "-s" or "-server"):
            i += 1
            config.serverAddress = getArgValue("server address", args, i)
            #TODO(maybe): check for address validity

        elif (args[i].lower() == "-httphost"):
            i += 1
            config.httpHost = getArgValue("HTTP host", args, i)

        elif (args[i].lower() == "-httpport"):
            i += 1
            port = getArgValue("HTTP port", args, i)
            try:
                config.httpPort = int(port)

            except:
                print("Failed to parse HTTP port to integer: " + port)
                exit()

        elif (args[i].lower() == "-b" or "-blender" or "-blenderpath"):
            i += 1
            config.blenderPath = getArgValue("blender path", args, i)
            config.blenderPath = checkBlenderPath(config.blenderPath)

    if (dumpConfig):
        config.saveToJson(CONFIG_JSON_PATH)


def main():
    start_client("localhost", 65432)
    return

    global config

    config = WCConfig.WCConfig()
    config.readFromJson(CONFIG_JSON_PATH)

    parseArgs(sys.argv)

    if (autoRegister):
        register()

    loop()

main()