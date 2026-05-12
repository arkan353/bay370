"""shortdb — работа с короткими ссылками (SQLAlchemy + SQLite)."""

from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import String, Integer, DateTime, func, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session
import sqlProtect

#TODO: добавить проверку на банворды а так же логирование ДБ

# ── Базовый класс ──────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Модель ссылки ──────────────────────────────────────────────────

class Link(Base):
    __tablename__ = "links"

    id: Mapped[int] = mapped_column(primary_key=True)
    original_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    short_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False, index=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    clicks: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
    )


# ── Подключение к БД ───────────────────────────────────────────────

_engine = create_engine("sqlite:///short_links.db", echo=False)


def init_db():
    """Создать таблицы, если их нет."""
    Base.metadata.create_all(_engine)


def _get_session() -> Session:
    return Session(_engine)

# ── Проверка на запрещенные слова ───────────────────────────────────────
def check_for_banned_words(text: str) -> bool:
    """Проверить текст на наличие запрещённых слов."""
    banned_words = sqlProtect.get_banned_words()
    text_lower = text.lower()
    return any(banned_word in text_lower for banned_word in banned_words)

# ── Функции для работы со ссылками ─────────────────────────────────



def create_short_link(
    original_url: str,
    short_code: str,
    password_hash: Optional[str] = None,
) -> Link:
    """Создать новую короткую ссылку."""
    if check_for_banned_words(original_url):
        raise ValueError("Original URL contains banned words.")
    link = Link(
        original_url=original_url,
        short_code=short_code,
        password_hash=password_hash,
    )
    with _get_session() as session:
        session.add(link)
        session.commit()
        # возвращаем свежую копию с БД (чтобы id и created_at были заполнены)
        session.refresh(link)
        return link


def get_short_link(short_code: str) -> Optional[Link]:
    """Получить ссылку по короткому коду."""
    if check_for_banned_words(short_code):
        raise ValueError("Short code contains banned words.")

    with _get_session() as session:
        return session.query(Link).filter(Link.short_code == short_code).first()



def increment_clicks(short_code: str) -> Optional[Link]:
    """Увеличить счётчик переходов."""
    if check_for_banned_words(short_code):
        raise ValueError("Short code contains banned words.")

    with _get_session() as session:
        link = session.query(Link).filter(Link.short_code == short_code).first()
        if link:
            link.clicks += 1
            session.commit()
            session.refresh(link)
        return link


def link_exists(short_code: str) -> bool:
    """Проверить, занят ли короткий код."""
    if check_for_banned_words(short_code):
        raise ValueError("Short code contains banned words.")
    with _get_session() as session:
        return session.query(Link).filter(Link.short_code == short_code).first() is not None


def get_stats(short_code: str) -> Optional[dict]:
    """Получить статистику по ссылке."""
    if check_for_banned_words(short_code):
        raise ValueError("Short code contains banned words.")
    link = get_short_link(short_code)
    if not link:
        return None
    return {
        "original_url": link.original_url,
        "short_code": link.short_code,
        "clicks": link.clicks,
        "created_at": link.created_at.isoformat() if link.created_at else None,
        "is_protected": link.password_hash is not None,
    }
