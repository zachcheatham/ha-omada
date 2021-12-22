class OmadaApiException(Exception):
    pass

class HttpErrorCode(OmadaApiException):
    def __init__(self, *args: object, url: str, code: str, msg: str="") -> None:
        self.code = code
        self.msg = msg
        super().__init__(f"Call to {url} received status code {code}: {msg}")
class LoginRequired(OmadaApiException):
    pass

class LoginFailed(OmadaApiException):
    pass
class RequestError(OmadaApiException):
    pass
class InvalidURLError(RequestError):
    pass
class SSLError(RequestError):
    pass
class OperationForbidden(RequestError):
    pass
class UnknownSite(RequestError):
    pass

API_ERRORS = {
    -30109: LoginFailed,
    -1600: RequestError,
    -1005: OperationForbidden,
}

def raise_response_error(url, response):
    exc = API_ERRORS.get(response["errorCode"])
    if exc != None:
        raise exc(response["msg"])
    
    raise HttpErrorCode(url=url, code=response["errorCode"], msg=response["msg"])