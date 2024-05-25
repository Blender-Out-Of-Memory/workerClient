import os
import sys
import time
import socket
import pickle
import platform
import subprocess
import http.client
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

import WCConfig
import CommunicationConstants as CConsts

CONFIG_JSON_PATH = "config.json"

config: WCConfig.WCConfig
isRegistered: bool = False

workingThread: Thread = None
listenerThread: Thread = None

class WorkerHTTPRequestHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        print("Got request for " + self.path)
        if self.path == CConsts.STARTTASK:
            global workingThread
            if (workingThread is not None and workingThread.isAlive()):
                print(f"Worker thread already running. Ignoring \"{CConsts.STARTTASK}\" request") #TODO:(maybe) implement queueing
                self.send_error(500, f"Worker already working. Ignored request")
                return

            headers = self.headers
            #try:
            #    headers = self.headers
            #except Exception as ex:
            #    print(f"Failed to decode \"{CConsts.STARTTASK}\" request body (to dict)")
            #    print("Exception: " + str(ex))
            #    self.send_error(500, f"Failed to decode \"{CConsts.STARTTASK}\" request body (to dict)")
            #    return

            if (("task-id" and "file" and "start_frame" and "end_frame") in headers):
                workingThread = Thread(target=runTask, args=(headers["task-id"], headers["file"], headers["start_frame"], headers["end_frame"]))
                workingThread.start()
                print("Started working thread")
                self.send_response(200)
                self.end_headers() # necessary to send
                return
            else:
                print("Missing information in request body")
                self.send_error(500, f"Missing information in request body")
                return

        else:
            print("Unknown request (path)")


def download_file(task_id: str, path: str) -> str:
    conn = http.client.HTTPConnection(config.serverAddress, config.serverPort)
    conn.request('GET', path)
    response = conn.getresponse()

    filename = task_id + ".blend"
    if response.status == 200:
        with open(filename, 'wb') as file:
            file.write(response.read())
        print('Downloaded file successfully.')
        return filename
    else:
        print(f'Error downloading file: {response.status} {response.reason}')
        filename = ""

    conn.close()
    return filename

def runBlender(file: str, start_frame: int, end_frame: int):
    command = "\"" + config.blenderPath + "\""
    command += " \"" + os.path.abspath(file) + "\""
    command += " " + config.blenderArgs #TODO: check for invalid and disallowed args (like changing output format)
    command += " -o \"" + config.outputPath + "\""
    command += " -s " + str(start_frame)
    command += " -e " + str(end_frame)
    command += " -b" #doesn't work without
    command += " -a"

    #command = ["\"" + config.blenderPath + "\"",
    #            file,
    #            config.blenderArgs, #TODO: check for invalid and disallowed args (like changing output format)
    #            "-o",
    #            config.outputPath,
    #            "-s",
    #            str(start_frame),
    #            "-e",
    #            str(end_frame),
    #            "-b", #doesn't work without
    #            "-a"]

    print("Launching Blender with command: " + str(command))

    subprocess.run(command, shell=True)
    print("Finished Blender --------------------------------------------------------")

def runTask(task_id: str, file: str, start_frame: int, end_frame: int):
    print("CWD in runTask: " + os.getcwd())

    filename = download_file(task_id, file)
    print(f"Does {filename} exist? " +  str(os.path.exists(filename)))
    if (filename == ""):
        print("Ending thread as no file was downloaded")
        return

    runBlender(filename, start_frame, end_frame)

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

def listen(host: str, port: int):
    server_address = (host, port)
    httpd = HTTPServer(server_address, WorkerHTTPRequestHandler)
    print(f'Listener runs at {host}:{port}')
    httpd.serve_forever()
    return

def register():
    #Register at server as available worker
    connection = http.client.HTTPConnection(config.serverAddress, config.serverPort)
    data = {"Action": CConsts.REGISTER, "Host": config.httpHost, "Port": config.httpPort}
    connection.request('GET', CConsts.WORKERMGMT, headers=data) #TODO:send WorkerID if already assigned one
    response = connection.getresponse()

    #Check if response belongs to request??
    if response.status == 200:
        responseData = response.read()
        print("Registration sucessful: " + responseData.decode("utf-8"))
        global isRegistered
        isRegistered = True
    else:
        print(f'Registration failed: {response.status} {response.reason}')

    connection.close()
    #Start thread to listen to tasks
    global listenerThread
    listenerThread = Thread(target=listen, args=(config.httpHost, config.httpPort))
    listenerThread.start()
    return

def loop():
    print("Entered loop")
    stop = False
    while not stop:
        inp = input("Enter command> ")
        if (inp.lower() == ("r" or "register")):
            if (isRegistered):
                print("Already registered")
            else:
                register()
        elif (inp.lower() == ("q" or "quit")):
            stop = True
        elif (inp.lower() == ("fq" or "forcequit")):
            #send forcequitted to server
            exit()
        elif (inp.lower() == ("sc" or "showconfig")):
            global config
            print(config.__dict__)
        else:
            print("Unknown command")

        inp = ""

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
        if (args[i].lower() == ("-h" or "-help")):
            print("Available command line arguments:")

        elif (args[i].lower() == ("-d" or "-dump" or "-dc" or "-dumpconfig")):
            dumpConfig = True

        elif (args[i].lower() == ("-ar" or "-autoregister")):
            config.autoRegister = True

        elif (args[i].lower() == ("-s" or "-server")):
            i += 1
            config.serverAddress = getArgValue("server address", args, i)
            #TODO(maybe): check for address validity

        elif (args[i].lower() == ("-p" or "-port")):
            i += 1
            port = getArgValue("server port", args, i)
            try:
                config.serverPort = int(port)
            except:
                print("Failed to parse server port to integer: " + port)
                exit()

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

        elif (args[i].lower() == ("-b" or "-blender" or "-blenderpath")):
            i += 1
            config.blenderPath = getArgValue("blender path", args, i)
            config.blenderPath = checkBlenderPath(config.blenderPath)

        elif (args[i].lower() == ("-ba" or "-bargs" or "-blenderargs")):
            i += 1
            config.blenderArgs = getArgValue("blender args", args, i)
            #Valiate blender args ??

    if (dumpConfig):
        config.saveToJson(CONFIG_JSON_PATH)


def main():
    print(sys.argv)
    #start_client("localhost", 65432)

    global config

    config = WCConfig.WCConfig()
    config.readFromJson(CONFIG_JSON_PATH)

    parseArgs(sys.argv)

    #runBlender("0000_0000_0000_0000.blend", 0, 50)

    if (config.autoRegister):
        register(config.serverAddress, config.serverPort)

    loop()


main()