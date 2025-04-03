from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel


SESSION_KEY = "5410040e731b9ff9bfd9df9659b431abf5930b9f662a4a62a98d15304fea9338"
ALGORITHM = "HS256"

TOKEN_EXPIRY_MINS = 30

Query_Set = {
    "sitanshu":{
        "first_name": "sitanshu",
        "last_name": "mohapatra",
        "username": "sitanshu",
        "hashed_pass": "$2b$12$CNWMi9fdFPK0/8OO1TswB.V4wurl6z8LBtDdr4ffJjL9Kr7gMKsay",
        "subscribed": True
    }
}

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    name: str | None = None

class User(BaseModel):
    first_name: str
    last_name: str | None = None
    username: str
    subscribed: bool | None = None

class UserinDB(User):
    hashed_pass: str

pwd_context = CryptContext(schemes=['bcrypt'], deprecated = "auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="api/token")

app = FastAPI()

def verify(asText: str, hashedPass: str):
    return pwd_context.verify(asText, hashedPass)

def hash_pass(asText: str) -> str:
    return pwd_context.hash(asText)

def get_user(db, username: str):
    if username:
        user_data = db[username]
        return UserinDB(**user_data)
    return None
    
def authenticate(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return None
    if not verify(password, user.hashed_pass):
        return None
    return user

def create_access_token(data: dict, expiry_delta: timedelta | None = None):
    to_encode = data.copy()
    if expiry_delta:
        expiry = (datetime.now() + expiry_delta).strftime("%H:%M:%S")
        # expiry = (datetime.now() + expiry_delta).time()
    else:
        expiry = (datetime.now() + timedelta(minutes=30)).strftime("%H:%M:%S")
        # expiry = (datetime.now() + timedelta(minutes=30)).time()
    to_encode["expiry"] = expiry
    encoded_jwt = jwt.encode(
                            to_encode, 
                            key=SESSION_KEY, 
                            algorithm=ALGORITHM
                        )
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth_2_scheme)):
    cred_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                    detail="Could not authorise credentials",
                                    headers={"WWW-Authenticate": "Bearer"},
                                    )
    try:
        payload = jwt.decode(token, key=SESSION_KEY, algorithms=ALGORITHM)
        username = payload.get("sub")
        if not username:
            raise cred_exception
        token_data = TokenData(name=username)
    except JWTError:
        raise cred_exception
    
    user = get_user(db = Query_Set, username= token_data.name)
    if not user:
        raise cred_exception
    
    return user

async def get_current_active_user(current_user: UserinDB = Depends(get_current_user)):
    if not current_user.subscribed:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="user not subscribed",
                            )
    return current_user

@app.post("/api/token", response_model= Token)
async def access_token_page(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate(db = Query_Set, 
                        username = form_data.username, 
                        password = form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="could not authenticate user",
                            headers={"WWW-Authenticate": "Bearer"})
    token_expiry = timedelta(minutes= TOKEN_EXPIRY_MINS)
    access_token = create_access_token(data={"sub":user.username},
                                        expiry_delta=token_expiry)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/{id}")
async def get_user_by_id(id: int, current_user: UserinDB = Depends(get_current_active_user)):
    user = current_user
    return {
        "id": id,
        "owner":user
    }
