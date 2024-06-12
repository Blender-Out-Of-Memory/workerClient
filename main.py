import os
import socket
import sys
import time
import platform
import subprocess
import http.client
from http.server import SimpleHTTPRequestHandler, HTTPServer
from threading import Thread

import WCConfig
from RenderTask import RenderTask, RenderOutputType
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

            task = RenderTask.from_headers(self.headers) # TODO: ensure self.headers is usable like a dictionary
            if (type(task) is str):
                print(task)
                self.send_error(500, f"Error during {CConsts.STARTTASK} header parsing: {task}")
                return

            # else: type(task) is RenderTask
            workingThread = Thread(target=run_task, args=(task,)) # comma after task to make it a tuple so it's iterable
            workingThread.start()
            print("Started working thread")
            self.send_response(200)
            self.end_headers()  # necessary to send

        else:
            self.send_error(404, f"Unknown request: {self.path}")
            print(f"Unknown request: {self.path}")


def download_file(task: RenderTask) -> bool:
    connection = http.client.HTTPConnection(task.FileServerAddress, task.FileServerPort)
    connection.request("GET", "blenderdata", headers={"Task-ID": task.TaskID})
    response = connection.getresponse()

    path = f"{task.get_folder()}/blenderfiles"
    if response.status == 200:
        os.makedirs(path, exist_ok=True)
        path += f"/{task.get_filename()}"
        with open(path, "wb+") as file:
            file.write(response.read())

        print("Downloaded file successfully.")
        success = True
    else:
        print(f"Error downloading file: {response.status} {response.reason}")
        success = False

    connection.close()
    return success

def evalute_blender_cl_output(message: str):
    num = ""

    if (message.startswith("Append frame")):  # for videos
        for i in range(len(message) - 2, 0, -1):  # -2 to skip \n
            if (not message[i].isdigit()):
                break

            num = message[i] + num

        return int(num)

    elif (message.startswith("Saved:")):  # for images
        readDigit = False
        for i in range(len(message) - 2, 0, -1):
            if (not message[i].isdigit()):
                if readDigit:
                    break
                else:
                    continue

            readDigit = True
            num = message[i] + num

        return int(num)

    return None

def send_render_output(task: RenderTask, frame: int):
    connection = http.client.HTTPConnection(config.serverAddress, config.serverPort)
    filepath = f"{task.get_folder()}/renderoutput/"
    if (frame == -1):  # video
        # filepath += ####-####
        filepath += f"{str(task.StartFrame).zfill(len(str(task.EndFrame)))}-{str(task.EndFrame).zfill(len(str(task.EndFrame)))}"
        frameInfo = f"{str(task.StartFrame)}-{str(task.EndFrame)}"

    else:
        # filepath += ####
        filepath += f"{str(frame).zfill(len(str(task.EndFrame)))}"
        frameInfo = str(frame)

    with open(filepath, "rb") as file:
        file.seek(0, os.SEEK_END)
        headers = {"Content-Type": "application/octet-stream", "Content-Length": str(file.tell()), "Task-ID": task.TaskID, "Worker-ID": "DEF", "Frame-Info": frameInfo}
        file.seek(0)
        connection.request("PUT", body=file.read(), headers=headers, url="")
    response = connection.getresponse()  # TODO:Add timeout and retry
    # TODO: Add error handling
    connection.close()
    print(f"Successfully sent frame(s) {frameInfo} to server")

def run_blender(task: RenderTask):
    command  = f"\"{config.blenderPath}\""
    command += f" \"{task.get_folder()}/blenderfiles/{task.get_filename()}\""
    command += f" {config.blenderArgs}"  # TODO: check for invalid and disallowed args (like changing output format)

    outputPath = f"{task.get_folder()}/renderoutput"
    os.makedirs(outputPath, exist_ok=True)
    outputPath += "/" + "#" * len(str(task.EndFrame))
    command += f" -o \"{outputPath}\""

    command += f" -x 0"
    command += f" -s {str(task.StartFrame)}"
    command += f" -e {str(task.EndFrame)}"
    command += f" -b"  # doesn't work without
    command += f" -a"


    print(f"Launching Blender with command: {str(command)}")

    blenderProcess = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    totalFrames = int((task.EndFrame - task.StartFrame) / task.FrameStep)
    lines = []
    writtenAnything = False
    blenderRunning = True
    while (blenderRunning):
        errorLine = blenderProcess.stderr.readline()
        if errorLine:
            print(errorLine)

        line = blenderProcess.stdout.readline()
        lines.append(line)
        if not line and blenderProcess.poll() is not None:  # read return code (has blender quit successfully)
            blenderRunning = False
        else:
            # print(line) # outsource to new terminal window to keep this one clean
            frame = evalute_blender_cl_output(line.decode("utf-8"))
            if (frame is not None):
                writtenAnything = True
                if not (task.OutputType.is_video()):
                    Thread(target=send_render_output, args=(task, frame)).start()
                relativeFrame = int((frame - task.StartFrame) / task.FrameStep)
                progress = (relativeFrame + 1) / (totalFrames + 1) * 100
                print(f"Frame {relativeFrame} / {totalFrames} | {frame} in {task.StartFrame} - {task.EndFrame} | {progress:.2f}%")

        time.sleep(0.1)

    if (task.OutputType.is_video()):
        Thread(target=send_render_output, args=(task, -1)).start()
    print("Finished Blender --------------------------------------------------------")
    if not writtenAnything:
        for line in lines:  # Probably error messages
            print(line)

def run_task(task: RenderTask):
    print("CWD in runTask: " + os.getcwd())

    downloaded = download_file(task)
    if not downloaded:
        print("Ending thread because no file was downloaded")
        return

    run_blender(task)

def listen(host: str, port: int):
    server_address = (host, port)
    httpd = HTTPServer(server_address, WorkerHTTPRequestHandler)
    print(f"Listener runs at {host}:{port}")
    httpd.serve_forever()
    return

def register():
    # Register at server as available worker
    MAX_RETRIES = 3
    TIMEOUT = 5  # timeout after x (here: 5) seconds
    retry_count = 0
    while retry_count < MAX_RETRIES:   # iterating through MAX_RETRIES possible retries
        connection = None   # ensuring connection is defined (for the finally block)
        try:
            # usual connection-work and response processing
            connection = http.client.HTTPConnection(config.serverAddress, config.serverPort, timeout=TIMEOUT)
            data = {"Action": CConsts.REGISTER, "Host": config.httpHost, "Port": config.httpPort}
            connection.request("GET", CConsts.WORKERMGMT, headers=data) # TODO:send WorkerID if already assigned one
            response = connection.getresponse()

            # Check whether response belongs to request??
            if response.status == 200:
                responseData = response.read()
                print("Registration sucessful: " + responseData.decode("utf-8"))
                global isRegistered
                isRegistered = True
            else:
                print(f"Registration failed: {response.status} {response.reason}")
        except socket.timeout as e:   # did response timeout?
            retry_count += 1
            print(f"Socket timeout, retrying {retry_count}/{MAX_RETRIES}...")
            if retry_count >= MAX_RETRIES:
                print("Max retries reached, unable to get response.")
        except http.client.HTTPException as e:
            print("HTTP exception:", e)
            break
        except Exception as e:
            print("Other exception:", e)
            break
        finally:
            # Close the connection if it was opened
            if connection is not None:
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

def check_blender_path(blenderPath: str):
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

def get_arg_value(message: str, args: list[str], index: int):
    if (index == len(args)):    
        print("No " + message + " specified after " + str(args[index - 1]))
        exit()

    return args[index]

def parse_args(args: list[str]):
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
            config.serverAddress = get_arg_value("server address", args, i)
            # TODO(maybe): check for address validity

        elif (args[i].lower() in {"-p", "-port"}):
            i += 1
            port = get_arg_value("server port", args, i)
            try:
                config.serverPort = int(port)
            except:
                print("Failed to parse server port to integer: " + port)
                exit()

        elif (args[i].lower() == "-httphost"):
            i += 1
            config.httpHost = get_arg_value("HTTP host", args, i)

        elif (args[i].lower() == "-httpport"):
            i += 1
            port = get_arg_value("HTTP port", args, i)
            try:
                config.httpPort = int(port)
            except:
                print("Failed to parse HTTP port to integer: " + port)
                exit()

        elif (args[i].lower() in {"-b", "-blender", "-blenderpath"}):
            i += 1
            config.blenderPath = get_arg_value("blender path", args, i)
            config.blenderPath = check_blender_path(config.blenderPath)

        elif (args[i].lower() in {"-ba", "-bargs", "-blenderargs"}):
            i += 1
            config.blenderArgs = get_arg_value("blender args", args, i)
            # Validate blender args ??

        elif (args[i].lower() in {"-o", "-out", "-output", "-outputpath"}):
            i += 1
            config.outputPath = get_arg_value("output path", args, i)

        else:
            print("Unknown argument: " + args[i])

        i += 1

    if (dumpConfig):
        config.saveToJson(CONFIG_JSON_PATH)


def main():
    global config

    config = WCConfig.WCConfig()
    config.readFromJson(CONFIG_JSON_PATH)

    parse_args(sys.argv)

    if (config.autoRegister):
        register()

    loop()


main()