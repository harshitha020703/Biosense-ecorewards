from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from PIL import Image
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
import json

from database import (
    SessionLocal,
    init_db,
    get_user_by_email,
    create_user,
    update_user_stats,
    create_history,
    get_history_for_user,
    User,
)

app = FastAPI(title="BIOSENSE – EcoRewards API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SECRET_KEY = "SUPER_SECRET_KEY_123456789"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain, hashed):
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict):
    data = data.copy()
    data.update({"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


class UserCreate(BaseModel):
    name: str
    email: str
    password: str


class UserLogin(BaseModel):
    email: str
    password: str


class UserProfile(BaseModel):
    name: str
    email: str
    points: int
    total: int
    bio: int
    nonbio: int


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


MODEL_PATH = "models/biosense_classifier.h5"
CLASS_NAMES_PATH = "models/class_names.json"

model = load_model(MODEL_PATH)
class_names = json.load(open(CLASS_NAMES_PATH))
IMG_SIZE = (224, 224)


def preprocess(image):
    image = image.resize(IMG_SIZE)
    arr = np.array(image) / 255.0
    return np.expand_dims(arr, 0)


@app.post("/register", response_model=TokenResponse)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_email(db, payload.email):
        raise HTTPException(400, "Email already exists")

    user = create_user(db, payload.name, payload.email, hash_password(payload.password))

    token = create_access_token({"sub": payload.email})
    return TokenResponse(access_token=token, user=UserProfile(
        name=user.name, email=user.email, points=user.points,
        total=user.total_classified, bio=user.bio_count, nonbio=user.nonbio_count
    ))


@app.post("/login", response_model=TokenResponse)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    user = get_user_by_email(db, payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "Incorrect email or password")

    token = create_access_token({"sub": user.email})
    return TokenResponse(access_token=token, user=UserProfile(
        name=user.name, email=user.email, points=user.points,
        total=user.total_classified, bio=user.bio_count, nonbio=user.nonbio_count
    ))


@app.get("/me", response_model=UserProfile)
def get_me(current_user: User = Depends(get_current_user)):
    return UserProfile(
        name=current_user.name,
        email=current_user.email,
        points=current_user.points,
        total=current_user.total_classified,
        bio=current_user.bio_count,
        nonbio=current_user.nonbio_count,
    )


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    img = Image.open(file.file).convert("RGB")
    arr = preprocess(img)
    pred = model.predict(arr)[0]

    idx = int(np.argmax(pred))
    waste = class_names[idx]
    conf = float(pred[idx] * 100.0)

    return {"class": waste, "confidence": conf}


@app.post("/update-points")
async def update_points(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    updated = update_user_stats(
        db, current_user,
        payload["points"], payload["total"],
        payload["bio"], payload["nonbio"]
    )
    create_history(
        db, updated,
        payload["predicted_class"],
        int(payload["confidence"]),
        payload["points_earned"]
    )
    return {"message": "OK"}


@app.get("/history")
async def history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return get_history_for_user(db, current_user)


init_db()
