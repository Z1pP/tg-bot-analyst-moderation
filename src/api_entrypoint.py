import uvicorn

from api.main import app
from config import settings

if __name__ == "__main__":
    uvicorn.run(app, host=settings.API_HOST, port=int(settings.API_PORT))
