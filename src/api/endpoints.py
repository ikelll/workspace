from src.utils import consts

AUTH_AUTHS = "/gorizontvs/rest/auth/auths"
AUTH_LOGIN = "/gorizontvs/rest/auth/login"
AUTH_LOGOUT = "/gorizontvs/rest/auth/logout"
AUTH_LOGIN_NEGOTIATE = "/gorizontvs/rest/auth/login_negotiate"

SERVICES_OVERVIEW = "/gorizontvs/rest/connection"
SERVICE_IMAGE_WEB = "/gorizontvs/webapi/img/gallery"

def service_transport(service_id: str, transport_id: str) -> str:
    return f"/gorizontvs/rest/connection/{service_id}/{transport_id}"

def service_image(image_id: str) -> str:
    return f"{SERVICE_IMAGE_WEB}/{image_id}"

HEADER_AUTH_TOKEN = "X-Auth-Token"
HEADER_CONTENT_TYPE = "Content-Type"
USER_AGENT = consts.USER_AGENT