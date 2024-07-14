from typing import Dict, Callable, Optional, Sequence, Any
from http.client import HTTPResponse
from http import HTTPMethod


# Default values
DEFAULT_TIMEOUT = 5.0
DEFAULT_RETRIES = 5


class Message:
	Method: HTTPMethod
	URL: str
	Headers: Dict
	bodyFilepath: str
	Timeout: float
	Retries: int

	OnSuccess: Optional[Callable[[HTTPResponse, Sequence], Any]]
	OnSuccessArgs: Sequence

	@property
	def Body(self):
		return open(self.bodyFilepath, "rb").read() if (self.bodyFilepath) else None

	def __init__(self, method: HTTPMethod, url: str,
				 headers: Dict, bodyFilepath: str = None,
				 retries: int = DEFAULT_RETRIES, timeout: float = DEFAULT_TIMEOUT,
				 onSuccess: Optional[Callable[[HTTPResponse, Sequence], Any]] = None, onSuccessArgs: Sequence = None):
		self.Method = method
		self.URL = url
		self.Headers = headers
		self.bodyFilepath = bodyFilepath
		self.Timeout = timeout
		self.Retries = retries
		self.OnSuccess = onSuccess
		self.OnSuccessArgs = onSuccessArgs
