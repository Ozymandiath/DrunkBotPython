from sqlalchemy import Float, String, Integer, Boolean, DateTime, func, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


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
    strength: Mapped[float] = mapped_column(Float, default=5)
    agility: Mapped[float] = mapped_column(Float, default=5)
    drunkenness: Mapped[float] = mapped_column(Float, default=0)
    is_searching: Mapped[bool] = mapped_column(Boolean, default=False)
    is_in_duel: Mapped[bool] = mapped_column(Boolean, default=False)
    fails: Mapped[int] = mapped_column(Integer, default=0)
    update_stat: Mapped[Date] = mapped_column(Date, default=func.date("1999-01-01"))
    drunk_date: Mapped[Date] = mapped_column(Date, default=func.date("1999-01-01"))


class Duel(Base):
    __tablename__ = 'duels'

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    challenger_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=False)
    opponent_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=False)
    status: Mapped[str] = mapped_column(String, default='pending')  # Статус дуэли: 'pending', 'accepted', 'rejected'
    winner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.user_id'), nullable=True)

    # Отношения для связи с таблицей пользователей
    challenger: Mapped['User'] = relationship('User', foreign_keys=[challenger_id])
    opponent: Mapped['User'] = relationship('User', foreign_keys=[opponent_id])
    winner: Mapped['User'] = relationship('User', foreign_keys=[winner_id], uselist=False, post_update=True)
