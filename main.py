from typing import Any, Dict, List
import json
import fastapi
from fastapi import status
from fastapi import Request, HTTPException
from fastapi.param_functions import Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse, Response, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from auth import UserAuthHandler
from datetime import datetime, timedelta

app: fastapi.FastAPI = fastapi.FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

html = Jinja2Templates(directory="templates")

"""connection = psycopg2.connect(
    dbname="poo",
    user="postgres",
    password=os.getenv("DB_PASSWORD"),
    host=os.getenv("DB_HOSTNAME")
)"""

#db = connection.cursor()

auth: UserAuthHandler = UserAuthHandler()

users: List[Dict[str, str]] = [{
    "email": "admin",
    "password": auth.hash("admin"),
    "admin": True
}]

class Item(BaseModel):
    name: str
    price: float
    is_offer: bool = None

class RegistrationModel(BaseModel):
    names: str
    lastnames: str
    street_address: str
    city: str
    department: str
    gender: str
    country_code: str
    phone: str
    email: str
    birthday: str
    password: str
    confirmation: str


@app.exception_handler(HTTPException)
async def http_exception(request: Request, exception: HTTPException):
    print(exception.status_code)
    if exception.status_code == status.HTTP_401_UNAUTHORIZED:
        response: RedirectResponse = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)

        if request.cookies.get("token", None) is not None:
            response.delete_cookie("token")

        if request.cookies.get("cart", None) is not None:
            response.delete_cookie("cart")

        return response

    if exception.status_code == status.HTTP_403_FORBIDDEN:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    return JSONResponse({"detail": exception.detail}, status_code=exception.status_code)


@app.get("/", response_class=HTMLResponse)
def index(request: Request, user=Depends(auth.login_optional)):
    context: Dict[str, Any] = {
        "request": request,
        "user": user
    }

    return html.TemplateResponse("index.html", context)

@app.get("/login", response_class=HTMLResponse)
def get_login(request: Request, user=Depends(auth.login_optional)):
    if user is not None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    context: Dict[str, Any] = {
        "request": request,
        "user": None
    }

    return html.TemplateResponse("login.html", context)

@app.get("/register", response_class=HTMLResponse)
def get_register(request: Request, user=Depends(auth.login_optional)):
    if user is not None:
        return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)

    context: Dict[str, Any] = {
        "request": request,
        "user": None
    }

    return html.TemplateResponse("register.html", context)

@app.post("/login")
async def post_login(request: Request, response: Response):
    form: Dict[str, str] = await request.form()
    user: Dict[str, str] = None

    for each_user in users:
        if each_user["email"] == form["email"]:
            user = each_user
            break

    if (user is None) or (not auth.verify(form["password"], user["password"])):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid username and/or password")
    
    token = auth.encode_token({
        "email": user["email"],
        "admin": user["admin"]
    })

    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="token", value=f"Bearer {token}", httponly=True)
    response.set_cookie(key="cart", value=json.dumps({}))

    return response

    db.execute("SELECT email FROM users WHERE email=%s AND hash=%s", form["email"])

    if len(db.fetchall()) == 0:
        pass
    
    return form["password"]

@app.get("/logout")
async def logout(request: Request, response: Response, user=Depends(auth.login_required)):
    response = RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(key="token")
    response.delete_cookie(key="cart")

    return response

@app.post("/register", response_class=RedirectResponse, status_code=201)
async def post_register(request: Request):
    form: Dict[str, str] = await request.form()
    
    for user in users:
        if user["email"] == form["email"]:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username is taken")

    password_hash: str = auth.hash(form["password"])
    users.append({
        "email": form["email"],
        "admin": False,
        "password": password_hash,
    })

    return RedirectResponse("/", status_code=status.HTTP_303_SEE_OTHER)
"""
    db.execute("SELECT email FROM users WHERE email=%s", form["email"])

    if len(db.fetchall()) > 1:
        pass

    db.execute("INSERT INTO users VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (form["names"], form["lastnames"]))
    print(await request.form())
    return await request.form()
"""

@app.get("/store", response_class=HTMLResponse)
def get_store(request: Request, user=Depends(auth.login_optional)):
    # db.execute("SELECT * FROM items)
    # items: List[Dict[str, Any]] = [item for item in db.fetchall()]
    items: List[Dict[str, Any]] = [
        {
            "id": 12335,
            "name": "Item",
            "price": 100.00,
            "image": "../static/images/idk.jpg",
            "available": 100,
            "description": "This is an item."
        }, {
            "id": 1234445,
            "name": "Item2",
            "price": 10.00,
            "image": "../static/images/idk.jpg",
            "available": 150,
            "description": "This is another item."
        }, {
            "id": 12355,
            "name": "Item3",
            "price": 20.00,
            "image": "../static/images/idk.jpg",
            "available": 0,
            "description": "This item is sold out."
        }, {
            "id": 123745,
            "name": "Item4",
            "price": 5.99,
            "image": "../static/images/idk.jpg",
            "available": 10,
            "description": "This is another item."
        }, {
            "id": 123745,
            "name": "Item5",
            "price": 100000.00,
            "image": "../static/images/idk.jpg",
            "available": 10000,
            "description": "This is the last item."
        }
    ]

    context: Dict[str, Any] = {
        "request": request,
        "user": user,
        "items": items
    }

    return html.TemplateResponse("/store.html", context)

@app.get("/item", response_class=HTMLResponse)
async def get_item(request: Request, user=Depends(auth.login_optional)):
    # db.execute("SELECT * FROM items WHERE id=%s", (id))
    # item: Dict[str, Any] = db.fetchone()

    context: Dict[str, Any] = {
        "request": request,
        "user": user,
        "item": {
            "id": request._query_params["id"],
            "name": "Item",
            "price": 100.00,
            "image": "../static/images/idk.jpg",
            "available": 100,
            "description": "This is an item."
        }
    }

    return html.TemplateResponse("/item.html", context)


@app.get("/getCart", response_class=HTMLResponse)
async def get_item(request: Request, user=Depends(auth.login_required)):
    cart: List[Dict[str, str]] = json.loads(request.cookies["cart"])
    
    context: Dict[str, Any] = {
        "request": request,
        "user": user,
        "cart": cart
    }

    return html.TemplateResponse("/cart.html", context)

@app.post("/addToCart", response_class=HTMLResponse)
async def get_item(request: Request, user=Depends(auth.login_required)):
    form: Dict[str, Any] = await request.form()

    # db.execute("SELECT * FROM items WHERE id=%s", (id))
    # item: Dict[str, Any] = db.fetchone()
    cart: List[Dict[str, Any]] = json.loads(request.cookies["cart"])

    if cart.get(form["id"], None) is None:
        cart[int(form["id"])] = {
            "amount": int(form["amount"]),
            "price": float(form["price"])
        }
    else:
        cart[form["id"]]["amount"] += int(form["amount"])

    response: Response = RedirectResponse(f"/item?id={form['id']}", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="cart", value=json.dumps(cart))

    return response

@app.get("/profile", response_class=HTMLResponse)
async def get_profile(request: Request, user=Depends(auth.login_required)):
    form: Dict[str, Any] = await request.form()
    # db.execute("SELECT * FROM items WHERE id=%s", (id))
    # item: Dict[str, Any] = db.fetchone()

    context: Dict[str, Any] = {
        "request": request,
        "user": user
    }

    return html.TemplateResponse("/todo.html", context)

@app.get("/admin", response_class=HTMLResponse)
async def get_profile(request: Request, user=Depends(auth.admin_required)):
    form: Dict[str, Any] = await request.form()
    # db.execute("SELECT * FROM items WHERE id=%s", (id))
    # item: Dict[str, Any] = db.fetchone()

    context: Dict[str, Any] = {
        "request": request,
        "user": user
    }

    return html.TemplateResponse("/admin.html", context)

@app.get("/protected")
def protected(user=Depends(auth.login_required)):
    return {
        "user": user
    }

@app.get("/items/{item_id}")
def read_item(item_id: int, q: str = None):
    return {
        "item_id": item_id,
        "q": q
    }

@app.put("/items/{item_id}")
def update_item(item_id: int, item: Item):
    return {
        "item_name": item.name,
        "item_id": item_id
    }