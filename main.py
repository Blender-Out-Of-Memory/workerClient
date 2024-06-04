import os
import sys
import time
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
                print(f"Worker thread already running. Ignoring \"{CConsts.STARTTASK}\" request")  # TODO:(maybe) implement queueing
                self.send_error(500, f"Worker already working. Ignored request")
                return

            headers = self.headers

            if (all(field in headers for field in ("task-id", "file", "start_frame", "end_frame", "frame_step"))):
                try:
                    start_frame = int(headers["start_frame"])
                    end_frame = int(headers["end_frame"])
                    frame_step = int(headers["frame_step"])
                except:
                    print("Failed to parse frame range to int")
                    self.send_error(500, f"Failed to parse frame range to int")
                    return
                workingThread = Thread(target=runTask, args=(headers["task-id"], headers["file"], start_frame, end_frame, frame_step))
                workingThread.start()
                print("Started working thread")
                self.send_response(200)
                self.end_headers()  # necessary to send
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

def evaluteBlenderCLOutput(message: str):
    num = ""

    if (message.startswith("Append frame")):
        for i in range(len(message) - 2, 0, -1):  # -2 to skip \n
            if (not message[i].isdigit()):
                break

            num = message[i] + num

        return int(num)

    return None

def runBlender(file: str, start_frame: int, end_frame: int, frame_step: int):
    command = "\"" + config.blenderPath + "\""
    command += " \"" + os.path.abspath(file) + "\""
    command += " " + config.blenderArgs  # TODO: check for invalid and disallowed args (like changing output format)
    command += " -o \"" + config.outputPath + "\""
    command += " -s " + str(start_frame)
    command += " -e " + str(end_frame)
    command += " -b"  # doesn't work without
    command += " -a"


    print("Launching Blender with command: " + str(command))

    blenderProcess = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,)
    totalFrames = int((end_frame - start_frame) / frame_step)
    while (True):
        line = blenderProcess.stdout.readline()
        if not line and blenderProcess.poll() is not None:
            break
        else:
            # print(line) # outsource to new terminal window to keep this one clean
            frame = evaluteBlenderCLOutput(line.decode("utf-8"))
            if (frame is not None):
                relativeFrame = int((frame - start_frame) / frame_step)
                progress = (relativeFrame + 1) / (totalFrames + 1) * 100
                print(f"Frame {relativeFrame} / {totalFrames} | {frame} in {start_frame} - {end_frame} | {progress:.2f}%")

        time.sleep(0.05)  # TODO: increase sleep time and skip printint for frames rendered in the meantime

    print("Finished Blender --------------------------------------------------------")

def runTask(task_id: str, file: str, start_frame: int, end_frame: int, frame_step: int):
    print("CWD in runTask: " + os.getcwd())

    filename = download_file(task_id, file)
    print(f"Does {filename} exist? " +  str(os.path.exists(filename)))
    if (filename == ""):
        print("Ending thread as no file was downloaded")
        return

    runBlender(filename, start_frame, end_frame, frame_step)

def listen(host: str, port: int):
    server_address = (host, port)
    httpd = HTTPServer(server_address, WorkerHTTPRequestHandler)
    print(f'Listener runs at {host}:{port}')
    httpd.serve_forever()
    return

def register():
    # Register at server as available worker
    connection = http.client.HTTPConnection(config.serverAddress, config.serverPort)
    data = {"Action": CConsts.REGISTER, "Host": config.httpHost, "Port": config.httpPort}
    connection.request('GET', CConsts.WORKERMGMT, headers=data) # TODO:send WorkerID if already assigned one
    response = connection.getresponse() # TODO:Add timeout and retry

    # Check if response belongs to request??
    if response.status == 200:
        responseData = response.read()
        print("Registration sucessful: " + responseData.decode("utf-8"))
        global isRegistered
        isRegistered = True
    else:
        print(f'Registration failed: {response.status} {response.reason}')

    connection.close()
    # Start thread to listen to tasks
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
            # Quit after current task finishes (if one is running)
            stop = True # Placeholder
        elif (inp.lower() == ("fq" or "forcequit")):
            # Send forcequitted to server and cancel current task
            exit()
        elif (inp.lower() == ("sc" or "showconfig")):
            global config
            print(config.__dict__)
        else:
            print("Unknown command")

        inp = ""
        time.sleep(0.05)  # reduce performance impact of while(True)-loop

def checkBlenderPath(blenderPath: str):
    if os.name == "nt":
        if os.path.isdir(blenderPath):
            blenderPath = os.path.join(blenderPath, "blender.exe")
        
        # else if isfile(blenderPath):
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
            # TODO: Test if <blenderPath> is definitely an executable progra
    else:  # java (?)
        print("Unsupported platform: " + os.name)
        exit()
    
    return blenderPath

def getArgValue(message: str, args: list[str], index: int):
    if (index == len(args)):    
        print("No " + message + " specified after " + str(args[index - 1]))
        exit()

    return args[index]

def parseArgs(args: list[str]):
    global config
    dumpConfig: bool = False
    print(args)

    i = 1
    while i < len(args):  # instead of for-loop because setting i inside the loop wouldn't affect iterator variable i
        if (args[i].lower() in {"-h", "-help"}):
            print("Available command line arguments:")

        elif (args[i].lower() in {"-d", "-dump", "-dc", "-dumpconfig"}):
            dumpConfig = True

        elif (args[i].lower() in {"-ar", "-autoregister"}):
            config.autoRegister = True

        elif (args[i].lower() in {"-s", "-server"}):
            i += 1
            config.serverAddress = getArgValue("server address", args, i)
            # TODO(maybe): check for address validity

        elif (args[i].lower() in {"-p", "-port"}):
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

        elif (args[i].lower() in {"-b", "-blender", "-blenderpath"}):
            i += 1
            config.blenderPath = getArgValue("blender path", args, i)
            config.blenderPath = checkBlenderPath(config.blenderPath)

        elif (args[i].lower() in {"-ba", "-bargs", "-blenderargs"}):
            i += 1
            config.blenderArgs = getArgValue("blender args", args, i)
            # Validate blender args ??

        elif (args[i].lower() in {"-o", "-out", "-output", "-outputpath"}):
            i += 1
            config.outputPath = getArgValue("output path", args, i)

        else:
            print("Unknown argument: " + args[i])

        i += 1

    if (dumpConfig):
        config.saveToJson(CONFIG_JSON_PATH)


def main():
    global config

    config = WCConfig.WCConfig()
    config.readFromJson(CONFIG_JSON_PATH)

    parseArgs(sys.argv)

    if (config.autoRegister):
        register()

    loop()


main()