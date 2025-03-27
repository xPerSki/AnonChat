from os import getenv

import uvicorn
from bson import ObjectId
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo import MongoClient

DB_PASSWORD = getenv("DB_PASSWORD")
uri = f"mongodb+srv://persky:{DB_PASSWORD}@cluster0.jevvu.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client["forum_db"]
collection_posts = db["posts"]
collection_users = db["users"]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Post(BaseModel):
    id: str
    title: str
    content: str
    author_id: str


class User(BaseModel):
    user_id: str
    username: str
    password: str


@app.get("/")
def home(request: Request):
    posts = list(collection_posts.find())
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts})


@app.get("/create", response_class=HTMLResponse)
def create_post_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


@app.post("/create", response_class=HTMLResponse)
def create_post(request: Request, title: str = Form(...), content: str = Form(...)):
    new_post = {
        "id": str(ObjectId()),
        "title": title,
        "content": content,
        "author_id": "Anonymous"
    }
    collection_posts.insert_one(new_post)
    return templates.TemplateResponse("create_success.html", {"request": request})


@app.delete("/delete/{post_id}")
def delete_post(request: Request, post_id: str):
    result = collection_posts.delete_one({"id": post_id})
    if result.deleted_count == 1:
        return {"result": "Post deleted"}
    return {"result": "Post can't be deleted"}


@app.get("/get-post/{post_id}")
def get_post(request: Request, post_id: str):
    post = collection_posts.find_one({"id": post_id})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@app.get("/get-user/{user_id}")
def get_user(request: Request, user_id: str):
    user = collection_users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
