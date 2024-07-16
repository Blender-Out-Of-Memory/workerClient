import os
import re
from http import HTTPStatus
from typing import Tuple, Dict

from Enums import RenderOutputType, BlenderDataType


def _is_valid_id(id: str, prefix: str) -> bool:
	pattern = prefix + r"[0-9a-fA-F]{4}_[0-9a-fA-F]{4}_[0-9a-fA-F]{4}_[0-9a-fA-F]{4}"
	return re.fullmatch(pattern, id) is not None


class Task:
	TaskID: str
	SubtaskIndex: int
	FileServerAddress: str
	FileServerPort: int
	DataType: BlenderDataType
	OutputType: RenderOutputType

	StartFrame: int
	EndFrame: int
	FrameStep: int

	def get_identifying_header(self, workerID: str) -> Dict:
		return {
			"Task-Id": self.TaskID,
			"Subtask-Index": self.SubtaskIndex,
			"Worker-Id": workerID
		}

	def get_folder(self):
		return os.path.abspath(f"tasks/{self.TaskID}")

	def get_render_result_path(self, frame: int):
		filepath = f"{self.get_folder()}/"
		if (frame == -1):  # video
			# filepath += ####-####
			filepath += f"{str(self.StartFrame).zfill(len(str(self.EndFrame)))}-{str(self.EndFrame).zfill(len(str(self.EndFrame)))}"

		else:
			# filepath += ####
			filepath += f"{str(frame).zfill(len(str(self.EndFrame)))}"

		return f"{filepath}{self.OutputType.get_extension()}"

	def get_blender_data_path(self):
		filename = "blenderdata." + ("blend" if (self.DataType == BlenderDataType.SingleFile) else "zip")
		return f"{self.get_folder()}/{filename}"

	@classmethod
	def from_headers(cls, headers) -> Tuple:
		difference = {"Task-Id", "Subtask-Index", "File-Server-Address", "File-Server-Port", "Blender-Data-Type", "Output-Type", "Start-Frame", "End-Frame", "Frame-Step"}.difference(headers)
		if difference:  # difference is not empty
			return (f"Missing header fields for creation of Task: {", ".join(difference)}", HTTPStatus.BAD_REQUEST)

		# Check TaskID
		taskID = headers["Task-Id"]
		if not _is_valid_id(taskID, "T-"):
			return ("Invalid TaskID", HTTPStatus.BAD_REQUEST)


		# Check SubtaskIndex
		try:
			subtaskIndex = int(headers["Subtask-Index"])
		except:
			return ("Invalid SubtaskIndex", HTTPStatus.BAD_REQUEST)


		# Check FileServerAddress
		# TODO
		fileServerAddress = headers["File-Server-Address"]

		# Check FileServerPort
		try:
			fileServerPort = int(headers["File-Server-Port"])
			if (fileServerPort < 0 or fileServerPort > 65535):
				raise ValueError(f"Port {fileServerPort} outside valid port range")
		except:
			return ("Invalid SubtaskIndex", HTTPStatus.BAD_REQUEST)


		# Check DataType
		try:
			dataType = BlenderDataType.from_identifier(headers["Blender-Data-Type"])
		except:
			return ("Invalid DataType", HTTPStatus.BAD_REQUEST)


		# Check OutputType
		try:
			outputType = RenderOutputType.from_identifier(headers["Output-Type"])
		except:
			return ("Invalid OutputType", HTTPStatus.BAD_REQUEST)


		# Check StartFrame
		try:
			startFrame = int(headers["Start-Frame"])
			if (startFrame < 0):
				raise ValueError("StartFrame may not be smaller than 0")
		except:
			return ("Invalid StartFrame", HTTPStatus.BAD_REQUEST)


		# Check EndFrame
		try:
			endFrame = int(headers["End-Frame"])
			if (endFrame < startFrame):
				raise ValueError("EndFrame may not be smaller than StartFrame")
		except:
			return ("Invalid EndFrame", HTTPStatus.BAD_REQUEST)


		# Check FrameStep
		try:
			frameStep = int(headers["Frame-Step"])
			if (frameStep < 0):
				raise ValueError("FrameStep may not be smaller than 0")
		except:
			return ("Invalid FrameStep", HTTPStatus.BAD_REQUEST)

		return ("Received task successfully", HTTPStatus.OK, cls(taskID, subtaskIndex, fileServerAddress, fileServerPort, dataType, outputType, startFrame, endFrame, frameStep))


	def __init__(self, taskID: str, subtaskIndex: int, fileServerAddress: str, fileServerPort: int, dataType: BlenderDataType, outputType: RenderOutputType, startFrame: int, endFrame: int, frameStep: int):
		self.TaskID = taskID
		self.SubtaskIndex = subtaskIndex
		self.FileServerAddress = fileServerAddress
		self.FileServerPort = fileServerPort
		self.DataType = dataType
		self.OutputType = outputType
		self.StartFrame = startFrame
		self.EndFrame = endFrame
		self.FrameStep = frameStep

