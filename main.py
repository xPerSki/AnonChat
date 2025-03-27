import uvicorn
from os import getenv
from bson import ObjectId
from fastapi import FastAPI, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from pymongo import MongoClient
from datetime import datetime

DB_PASSWORD = getenv("DB_PASSWORD")
BACKEND_APP = getenv("BACKEND_APP")
uri = f"mongodb+srv://persky:{DB_PASSWORD}@cluster0.jevvu.mongodb.net/?appName=Cluster0"
client = MongoClient(uri)
db = client["forum_db"]
collection_posts = db["posts"]
collection_comments = db["comments"]
collection_users = db["users"]

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


class Post(BaseModel):
    id: str
    title: str
    content: str
    author_id: str
    created_at: str


class Comment(BaseModel):
    id: str
    post_id: str
    content: str
    created_at: str


class User(BaseModel):
    user_id: str
    username: str
    password: str


@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    posts = list(collection_posts.find().sort("created_at", -1))
    for post in posts:
        post["_id"] = str(post["_id"])
    return templates.TemplateResponse("index.html", {"request": request, "posts": posts, "backend_app": BACKEND_APP})


@app.get("/post/{post_id}", response_class=HTMLResponse)
def get_post(request: Request, post_id: str):
    post = collection_posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post["_id"] = str(post["_id"])
    comments = list(collection_comments.find({"post_id": post_id}).sort("created_at", -1))
    for comment in comments:
        comment["_id"] = str(comment["_id"])
        comment["created_at"] = comment["created_at"].strftime("%H:%M")
    return templates.TemplateResponse("post.html", {"request": request, "post": post, "comments": comments, "backend_app": BACKEND_APP})


@app.post("/post/{post_id}/comment", response_class=HTMLResponse)
def add_comment(request: Request, post_id: str, content: str = Form(...)):
    new_comment = {
        "_id": ObjectId(),
        "post_id": post_id,
        "content": content,
        "created_at": datetime.now(),
    }
    collection_comments.insert_one(new_comment)
    return RedirectResponse(url=f"/post/{post_id}", status_code=303)


@app.get("/create", response_class=HTMLResponse)
def create_post_form(request: Request):
    return templates.TemplateResponse("create.html", {"request": request, "backend_app": BACKEND_APP})


@app.post("/create", response_class=HTMLResponse)
def create_post(request: Request, title: str = Form(...), content: str = Form(...)):
    new_post = {
        "_id": ObjectId(),
        "title": title,
        "content": content,
        "author_id": "Anonymous",
        "created_at": datetime.now(),
    }
    collection_posts.insert_one(new_post)
    return templates.TemplateResponse("create_success.html", {"request": request, "backend_app": BACKEND_APP})


@app.delete("/delete/{post_id}")
def delete_post(post_id: str):
    result = collection_posts.delete_one({"_id": ObjectId(post_id)})
    if result.deleted_count == 1:
        return {"result": "Post deleted"}
    return {"result": "Post can't be deleted"}


@app.get("/get-post/{post_id}", response_class=HTMLResponse)
def get_post(request: Request, post_id: str):
    post = collection_posts.find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    post["_id"] = str(post["_id"])
    return post


@app.get("/get-user/{user_id}", response_class=HTMLResponse)
def get_user(request: Request, user_id: str):
    user = collection_users.find_one({"user_id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


if __name__ == "__main__":
    uvicorn.run("main:app", reload=True)
