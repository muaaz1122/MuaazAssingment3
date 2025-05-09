from fastapi import APIRouter, Depends, HTTPException, Form, Request, Cookie
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from app.database import get_db
from app.models import Task, User
from datetime import datetime, date

router = APIRouter(prefix="/tasks", tags=["Tasks"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard")
def dashboard(request: Request, user_id: int = Cookie(None), db: Session = Depends(get_db)):
    if not user_id:
        return RedirectResponse(url="/users/login?message=Please%20log%20in", status_code=303)

    tasks = db.query(Task).filter(Task.owner_id == user_id).all()
    return templates.TemplateResponse("dashboard.html", {"request": request, "tasks": tasks})


@router.post("/add")
def add_task(
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    deadline: str = Form(...),
    user_id: int = Cookie(None),
    db: Session = Depends(get_db)
):
    if not user_id:
        return RedirectResponse(url="/users/login?message=Please%20log%20in", status_code=303)

    new_task = Task(
        title=title,
        description=description,
        priority=priority,
        deadline=datetime.strptime(deadline, "%Y-%m-%d"),
        owner_id=user_id
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    if new_task.deadline.date() == date.today():
        user = db.query(User).filter(User.id == user_id).first()
        subject = "Task Due Today Reminder"
        message = f"Hey {user.username}, your task '{new_task.title}' is due today!"
        send_email(user.email, subject, message)

    return RedirectResponse(url="/tasks/dashboard", status_code=303)


# ✅ Route to render the edit form
@router.get("/edit/{task_id}")
def edit_task_form(task_id: int, request: Request, user_id: int = Cookie(None), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")

    return templates.TemplateResponse("edit_task.html", {"request": request, "task": task})


# ✅ Handle the form submission for editing
@router.post("/edit/{task_id}")
def edit_task(
    task_id: int,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form(...),
    deadline: str = Form(...),
    user_id: int = Cookie(None),
    db: Session = Depends(get_db)
):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")

    task.title = title
    task.description = description
    task.priority = priority
    task.deadline = datetime.strptime(deadline, "%Y-%m-%d")

    db.commit()
    return RedirectResponse(url="/tasks/dashboard", status_code=303)


# ✅ Delete task endpoint
@router.get("/delete/{task_id}")
def delete_task(task_id: int, user_id: int = Cookie(None), db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id, Task.owner_id == user_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not authorized")

    db.delete(task)
    db.commit()
    return RedirectResponse(url="/tasks/dashboard", status_code=303)
