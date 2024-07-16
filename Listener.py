from threading import Thread
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, HTTPServer

from Manager import Manager, Status
from CustomHTTPStatus import CustomHTTPStatus
from Task import Task

class Listener(SimpleHTTPRequestHandler):
	def do_GET(self):
		if (Manager.Status == Status.Disconnected):
			self.send_response(CustomHTTPStatus.WORKER_NOT_REGISTERED)
			self.end_headers()
			return

		if (self.path == "STARTTASK"):
			if (Manager.Status.value >= Status.Quitting.value):
				self.send_response(CustomHTTPStatus.WORKER_DOESNT_ACCEPT_NEW_TASKS, "Worker doesn't accept any new tasks")
				self.end_headers()
				return

			result = Task.from_headers(self.headers)
			self.send_response(result[1], result[0])
			self.end_headers()

			if (result[1] == HTTPStatus.OK):
				Manager.start_task(result[2])


	@staticmethod
	def start(host: str, port: int):
		server_address = (host, port)
		httpd = HTTPServer(server_address, Listener)
		print(f"Listener runs at {host}:{port}")
		httpd.serve_forever()