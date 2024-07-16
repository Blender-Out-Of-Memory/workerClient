import time
import subprocess
from http import HTTPMethod
from typing import Callable

from Task import Task
from Sender import Sender
import Message

# Provisional
import platform
BLENDER_PATH_BY_OS = {
	"Windows": "C:\\Program Files\\Blender Foundation\\Blender 4.1\\blender.exe",
	"Darwin": "/Applications/Blender.app/Contents/MacOS/Blender",
	"Linux": ""
}

class Worker:
	sendFrameCallback: Callable[[int], None] = None

	@staticmethod
	def run(getTaskCb: Callable[[], Task], sendFrameCb: Callable[[int], None]):
		Worker.sendFrameCallback = sendFrameCb

		while True:
			task = getTaskCb()
			Worker.run_blender(task)

	@staticmethod
	def evaluate_blender_cl_output(message: str):
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
	@staticmethod
	def run_blender(task: Task):
		command = f"\"{BLENDER_PATH_BY_OS[platform.system()]}\""
		command += f" \"{task.get_blender_data_path()}\""  # TODO: add case of .zip files

		outputPath = f"{task.get_folder()}"
		outputPath += "/" + "#" * len(str(task.EndFrame))
		command += f" -o \"{outputPath}\""

		command += f" -x 1"
		command += f" -s {str(task.StartFrame)}"
		command += f" -e {str(task.EndFrame)}"
		command += f" -b"  # doesn't work without
		command += f" -a"

		print(f"Launching Blender with command: {str(command)}")

		blenderProcess = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
		totalFrames = int((task.EndFrame - task.StartFrame) / task.FrameStep) + 1
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
				frame = Worker.evaluate_blender_cl_output(line.decode("utf-8"))
				if (frame is not None):
					writtenAnything = True
					if not task.OutputType.is_video():
						Worker.sendFrameCallback(frame)
					relativeFrame = int((frame - task.StartFrame) / task.FrameStep) + 1
					progress = relativeFrame / totalFrames * 100
					print(f"Frame {relativeFrame} / {totalFrames} | {frame} in {task.StartFrame} - {task.EndFrame} | {progress:.2f}%")

			time.sleep(0.1)

		if (task.OutputType.is_video()):
			Worker.sendFrameCallback(-1)
		print("Finished Blender --------------------------------------------------------")
		if not writtenAnything:
			for line in lines:  # Probably error messages
				print(line)
