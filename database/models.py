from sqlalchemy import Float, String, Integer, Boolean, DateTime, func, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    created: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    updated: Mapped[DateTime] = mapped_column(DateTime, default=func.now(), onupdate=func.now())

class User(Base):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    username: Mapped[str] = mapped_column(String, nullable=False)
    level: Mapped[int] = mapped_column(Integer, default=1)
    experience: Mapped[int] = mapped_column(Integer, default=0)
    health: Mapped[int] = mapped_column(Integer, default=100)
    strength: Mapped[int] = mapped_column(Integer, default=10)
    agility: Mapped[int] = mapped_column(Integer, default=10)
    drunkenness: Mapped[int] = mapped_column(Float, default=0)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=False)
    is_in_duel: Mapped[bool] = mapped_column(Boolean, default=False)
    update_stat: Mapped[Date] = mapped_column(Date, default=func.date("1999-01-01"))

