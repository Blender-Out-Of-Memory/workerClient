from enum import IntEnum

class CustomHTTPStatus(IntEnum):
	WORKER_NOT_REGISTERED = 560
	WORKER_DOESNT_ACCEPT_NEW_TASKS = 561