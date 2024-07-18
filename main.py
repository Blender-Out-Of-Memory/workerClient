import time
from threading import Thread

from Listener import Listener
from Sender import Sender
from Manager import Manager
import Message

# Default values for command line arguments
HOST = "0.0.0.0"
PORT = 8001

SERVER_HOST = "localhost"
SERVER_PORT = 8000


def main():
	# TODO: parse args
	listenerThread = Thread(target=Listener.start, args=(HOST, PORT), daemon=True)
	listenerThread.start()

	senderThread = Thread(target=Sender.start, args=(SERVER_HOST, SERVER_PORT), daemon=True)
	senderThread.start()

	Manager.register(HOST, PORT)  # at server

	while True:
		time.sleep(0.1)


main()
