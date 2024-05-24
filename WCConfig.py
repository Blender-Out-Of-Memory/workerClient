import os
import json
import pathlib

from typing import Dict


class WCConfig:
    blenderPath:    str  = ""
    blenderArgs:    str  = ""
    outputPath:     str  = "/out/" #TODO:set default value #HINT: // at start means relative to blend file
    serverAddress:  str  = ""  # TODO:set default value
    serverPort:     int  = 8000
    httpHost:       str  = ""  # TODO:set default value
    httpPort:       int  = -1  # TODO:set default value
    autoRegister:   bool = False

    def __init__(self, blenderPath: str, blenderArgs: str, outputPath: str, serverAddress: str, serverPort: int, httpHost: str, httpPort: int, autoRegister: bool):
        self.blenderPath    = blenderPath
        self.blenderArgs    = blenderArgs
        self.outputPath     = outputPath
        self.serverAddress  = serverAddress
        self.serverPort     = serverPort
        self.httpHost       = httpHost
        self.httpPort       = httpPort
        self.autoRegister   = autoRegister

    def __init__(self): return

    def readFromJson(self, path):
        try:
            with open(path, "r") as file:
                data = json.load(file)

            for attr in filter(lambda a: not a.startswith('__'), dir(WCConfig)):
                if attr in data:
                    setattr(self, attr, data[attr])

        except Exception as ex:
            cwd = pathlib.Path().resolve()
            print("Failed to parse " + os.path.join(cwd, "config.json"))
            print("Exception: " + str(ex))

    def saveToJson(self, path):
        try:
            with open(path, "w") as file:
                json.dump(self.__dict__, file, indent=4)

        except Exception as ex:
            print("Failed to write to config.json")
            print("Exception: " + str(ex))