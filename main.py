import sqlite3
from http.client import HTTPException
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
import os
from ApplicationDataManager import ApplicationDataManager


SECRET_KEY = "7ce3d09fb5e0eaa0c3e6769930c310ae0cc34276545a761c3fdc923aa04beca5"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

fake_users_db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin",
        "email": "admin@localhost.com",
        "hashed_password": "$2b$12$NO6HqKMp7Q5M1IZj2cSDteWUD3fT6kzbSA0w9Amp5GMhCQCWEH.qe", # secret
        "disabled": False,
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str = None

class User(BaseModel):
    username: str
    email: str = None
    full_name: str = None
    disabled: bool = None

class UserInDB(User):
    hashed_password: str

pwd_context = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


app = FastAPI()
# Allow CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def verify_password(plain_password, hashed_password):
    print(pwd_context.hash('secret'))
    print(plain_password, hashed_password)
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(db, username: str):
    if username in db:
        user_dict = db[username]
        return UserInDB(**user_dict)

def authenticate_user(fake_db, username: str, password: str):
    user = get_user(fake_db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(fake_users_db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

async def get_current_active_user(current_user: User = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user

## DATABASE AND DATA MANAGEMENT
conn = sqlite3.connect(os.getenv('DB_PATH') or 'db.sqlite3')
applicationDataManager = ApplicationDataManager(conn)

@app.get("/")
def read_root():
    # Testing to retrieve user list from the database
    applications = applicationDataManager.getCollection()
    return applications

# A route to exchange username and password for an access token
@app.post("/token")
async def login_for_access_token(
        form_data: OAuth2PasswordRequestForm = Depends()
):
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# URL For getting current user information
@app.get("/users/current")
async def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user

# URL For adding a new application, handle POST request sending json
@app.post("/applications/")
async def create_application(application: dict):
    id = applicationDataManager.insert(application)
    return {id: id}

# URL for getting the list of all applications
@app.get("/applications/")
async def read_applications(
        current_user: User = Depends(get_current_active_user)
):
    applications = applicationDataManager.getCollection()
    return {"data": applications, "count": len(applications)}

# URL for updating an application
@app.put("/applications/")
async def update_application(application: dict):
    id = applicationDataManager.update(application)
    return {id: id}

# URL for deleting an application
@app.delete("/applications/{id}")
async def delete_application(
        id: int,
        current_user: User = Depends(get_current_active_user)
):
    applicationDataManager.delete(id)
    return {id: id}

# URL for getting CSV file of all applications
from fastapi.responses import PlainTextResponse

@app.get("/applications/export")
async def export_applications(
        current_user: User = Depends(get_current_active_user),
        response_class=PlainTextResponse
):
    file_name = applicationDataManager.exportCSV()
    data = open(file_name, 'r').read()
    response = PlainTextResponse(content=data)
    response.headers["Content-Disposition"] = f"attachment; filename={file_name}"
    return response
