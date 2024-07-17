import http.client
import time
from queue import Queue
from threading import Thread

from Message import Message

SENDER_SLEEP_TIME = 0.1


class Sender:
	host: str = None
	port: int = None

	queue = Queue()
	priorityQueue = Queue()

	@staticmethod
	def send(message: Message) -> bool:
		success = False
		tries = 0
		print(f"Sending message {message.URL}")
		while (not success) and (message.Retries == -1 or tries < message.Retries):  # retry forever if Retries == -1
			try:
				connection = http.client.HTTPConnection(Sender.host, Sender.port, timeout=message.Timeout)
				connection.request(message.Method, message.URL, headers=message.Headers, body=message.Body)
				response = connection.getresponse()

				print("Got response: " + str(response.status))
				# print(response.read(100).decode("utf-8", errors="replace"))

				if response.status == 200:
					success = True
					if (message.OnSuccess):
						try:
							message.OnSuccess(response, message.OnSuccessArgs)
						except:
							print(f"onSuccess for message {message.URL} caused an exception")
					connection.close()
				else:
					print(response.read(100))
					connection.close()  # close as early as possible
					time.sleep(0.5)
				# TODO: handle other statuses

			except Exception as ex:
				print(f"Exception occurred while trying to send message with URL {message.URL}")
				print(ex)
				time.sleep(1)

			tries += 1
		return success

	@staticmethod
	def loop():
		while True:
			time.sleep(SENDER_SLEEP_TIME)

			if not Sender.priorityQueue.empty():
				queue = Sender.priorityQueue
			elif not Sender.queue.empty():
				queue = Sender.queue
			else:
				continue

			message = queue.get()
			success = Sender.send(message)
			if not success:
				queue.put(message)
				# TODO: error handling

	@staticmethod
	def start(host: str, port: int):
		Sender.host = host
		Sender.port = port

		Sender.loop()

	@staticmethod
	def add_message(message: Message, prioritize: bool):
		if (prioritize):
			Sender.priorityQueue.put(message)
		else:
			Sender.queue.put(message)
