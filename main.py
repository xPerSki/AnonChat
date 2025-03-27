import uvicorn
import logging
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from os import getenv
from pymongo import MongoClient
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from bson import ObjectId

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
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/create")
def create_post(request: Request):
    return templates.TemplateResponse("create.html", {"request": request})


@app.post("/create")
def create_post(request: Request, post=Post):
    new_post = post.model_dump()
    result = collection_posts.insert_one(new_post)
    return {"id": str(result.inserted_id), "result": "Post created"}


@app.delete("/delete/{post_id}")
def get_post(request: Request, post_id: str):
    post = collection_posts.find_one({"id": ObjectId(post_id)})
    result = collection_posts.delete_one(post)
    if result.deleted_count == 1:
        return {"result": "Post deleted"}
    return {"result": "Post can't be deleted"}


@app.get("/get-post/{post_id}")
def get_post(request: Request, post_id: str):
    post = collection_posts.find_one({"id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    post["id"] = str(post["id"])
    return post


@app.get("/get-user/{user_id}")
def get_user(request: Request, user_id: str):
    user = collection_users.find_one({"user_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user["user_id"] = str(user["user_id"])
    return user


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
