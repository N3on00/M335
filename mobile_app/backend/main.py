import uvicorn

# Import DTOs so decorators run and routers get registered
from data import dto  # noqa: F401

from routing.routing import Routing


def create_app():
    return Routing().get_app()


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
