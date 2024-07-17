import os
from enum import Enum
from threading import Thread
from queue import Queue
from http.client import HTTPResponse, HTTPConnection
from http import HTTPMethod
from typing import Sequence

from Task import Task
import Message
from Sender import Sender
from Worker import Worker


class Status(Enum):
	Available = 0
	Working = 1
	Quitting = 2
	Disconnected = 3

	def is_registered(self):
		return self in (Status.Available, Status.Working)


class Manager:
	Status: Status = Status.Disconnected
	WorkerID: str = "?"

	workingThread: Thread = None
	currentTask: Task = None
	taskQueue: Queue = Queue()
	registering: bool = False

	@staticmethod
	def currently_rendering():
		return Manager.Status in (Status.Working, Status.Quitting)

	@staticmethod
	def send_frame(frame: int):
		headers = Manager.currentTask.get_identifying_header(Manager.WorkerID)
		headers["Frame"] = str(frame)
		message = Message.Message(HTTPMethod.GET, "/worker_manager/post-render-result/",
								  headers, retries=-1, bodyFilepath=Manager.currentTask.get_render_result_path(frame))

		Sender.add_message(message, False)
	@staticmethod
	def get_next_task():
		Manager.currentTask = None
		task = Manager.taskQueue.get()  # blocks until element in queue
		Manager.currentTask = task
		return task

	@staticmethod
	def registered(response: HTTPResponse, args: Sequence):
		Manager.Status = Status.Available
		# More error handling
		Manager.WorkerID = response.headers["Worker-Id"]

		print(f"Registered successfully with WorkerID {Manager.WorkerID}")
		Manager.registering = False
		if (Manager.Status == Status.Quitting):
			Manager.Status = Status.Working
		elif (Manager.Status == Status.Disconnected):
			Manager.Status = Status.Available

		Manager.workingThread = Thread(target=Worker.run, args=(Manager.get_next_task, Manager.send_frame))
		Manager.workingThread.start()

	@staticmethod
	def register(listenerHost: str, listenerPort: int):
		if Manager.Status.is_registered():
			print("Already registered")
			return

		if (Manager.registering):
			print("Already registering")
			return

		Manager.registering = True
		performanceScore = 1  # TODO: calculate from hardware specs
		registerMessage = Message.Message(HTTPMethod.GET, "/worker_manager/register/",
										  {"Worker-Id": "?", "Host": str(listenerHost), "Port": str(listenerPort), "Performance-Score": performanceScore},
										  retries=-1, onSuccess=Manager.registered)
		Sender.add_message(registerMessage, True)
	@staticmethod
	def download_file(response: HTTPResponse, args: Sequence):
		task: Task = args[0]
		try:
			os.makedirs(task.get_folder(), exist_ok=True)
			with open(task.get_blender_data_path(), "wb") as file:
				file.write(response.read())
			Manager.taskQueue.put(task)
		except Exception as ex:
			print(f"Downloading file for task {task.TaskID} failed")
			print(ex)
			# TODO: retry or restructuring of download process

	@staticmethod
	def start_task(task: Task):
		downloadRequest = Message.Message(HTTPMethod.GET, "/worker_manager/download-blender-data/", task.get_identifying_header(Manager.WorkerID),
								  timeout=5, retries=5,
								  onSuccess=Manager.download_file, onSuccessArgs=(task,))

		Sender.add_message(downloadRequest, False)


# TODO:
# - server side unregistration
# - stop task
