from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

DATABASE_URL = "sqlite:///./biosense.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)

    points = Column(Integer, default=0)
    total_classified = Column(Integer, default=0)
    bio_count = Column(Integer, default=0)
    nonbio_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    histories = relationship(
        "ClassificationHistory",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class ClassificationHistory(Base):
    __tablename__ = "classification_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    predicted_class = Column(String, nullable=False)
    confidence = Column(Integer, default=0)  # store as int %
    points_earned = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="histories")


def init_db():
    Base.metadata.create_all(bind=engine)


# ---------- Helpers ----------

def get_user_by_email(db, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()


def create_user(db, name: str, email: str, password_hash: str) -> User:
    new_user = User(
        name=name,
        email=email,
        password_hash=password_hash,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


def update_user_stats(
    db,
    user: User,
    points: int,
    total: int,
    bio: int,
    nonbio: int,
) -> User:
    user.points = points
    user.total_classified = total
    user.bio_count = bio
    user.nonbio_count = nonbio
    db.commit()
    db.refresh(user)
    return user


def create_history(
    db,
    user: User,
    predicted_class: str,
    confidence: int,
    points_earned: int,
):
    history = ClassificationHistory(
        user_id=user.id,
        predicted_class=predicted_class,
        confidence=confidence,
        points_earned=points_earned,
    )
    db.add(history)
    db.commit()
    db.refresh(history)
    return history


def get_history_for_user(db, user: User, limit: int = 20):
    return (
        db.query(ClassificationHistory)
        .filter(ClassificationHistory.user_id == user.id)
        .order_by(ClassificationHistory.created_at.desc())
        .limit(limit)
        .all()
    )
