from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.database import engine, Base
from dotenv import load_dotenv
from app.routes.users import router as users_router
from app.routes.tasks import router as tasks_router

# Load environment variables
load_dotenv()

app = FastAPI()

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="app/templates")

app.include_router(users_router)
app.include_router(tasks_router)


@app.get("/", response_class=RedirectResponse)
def home():
    return RedirectResponse(url="/users/login", status_code=307)
