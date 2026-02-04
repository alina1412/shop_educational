import uvicorn
from fastapi import FastAPI

from service.endpoints.data_handlers import api_router as data_routes

app = FastAPI()


app.include_router(data_routes)


if __name__ == "__main__":
    uvicorn.run("service.__main__:app", host="0.0.0.0", port=8000, reload=True)
