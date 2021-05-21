class OmadaApiException(Exception):
    pass

class LoginRequired(OmadaApiException):
    pass

class RequestError(OmadaApiException):
    pass

class LoginFailed(OmadaApiException):
    pass

API_ERRORS = {
    -30109: LoginFailed,
    -1600: RequestError
}

def raise_response_error(response):
    exc = API_ERRORS.get(response["errorCode"])
    if exc != None:
        raise exc(response["msg"])
    
    raise OmadaApiException("API Error Code {}: {}".format(response["errorCode"], response["msg"]))