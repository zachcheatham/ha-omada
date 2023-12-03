class OmadaApiException(Exception):
    pass


class LoginRequired(OmadaApiException):
    pass


class LoginFailed(OmadaApiException):
    pass


class RequestError(OmadaApiException):
    def __init__(self, url: str, msg: str) -> None:
        super().__init__(f"Call to {url} failed: {msg}")


class HttpErrorCode(RequestError):
    def __init__(self, *args: object, url: str, code: str, msg: str = "") -> None:
        self.code = code
        self.msg = msg
        super().__init__(url, f"Received status code {code}")


class APIErrorCode(RequestError):
    def __init__(self, *args: object, url: str, code: str, msg: str = "") -> None:
        self.code = code
        self.msg = msg
        super().__init__(url, f"API Error {code}: {msg}")


class RequestTimeout(RequestError):
    def __init__(self, url: str) -> None:
        super().__init__(url, "Timed out.")


class InvalidURLError(RequestError):
    pass


class SSLError(RequestError):
    pass


class OperationForbidden(RequestError):
    pass


class UnknownSite(RequestError):
    pass


class UnsupportedVersion(RequestError):
    pass


API_ERRORS = {
    -30109: LoginFailed,
    -1600: RequestError,
    -1005: OperationForbidden,
}


def raise_response_error(url, response):
    exc = API_ERRORS.get(response["errorCode"])
    if exc is not None:
        raise exc(url, response["msg"])

    raise APIErrorCode(url=url, code=response["errorCode"], msg=response["msg"])
