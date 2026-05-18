from datetime import datetime, timezone
from typing import Optional, Dict, Any
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, JSON
from sqlalchemy.dialects.postgresql import JSONB


class TrackedGame(SQLModel, table=True):
    __tablename__: str = "tracked_games"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(nullable=False)
    platform: str = Field(nullable=False)
    slug: str = Field(nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )


class PriceSnapshot(SQLModel, table=True):
    __tablename__: str = "price_snapshots"

    id: Optional[int] = Field(default=None, primary_key=True)
    game_id: int = Field(
        foreign_key="tracked_games.id",
        ondelete="CASCADE",
        nullable=False
    )
    min_price: float = Field(nullable=False)
    offers_json: Dict[str, Any] = Field(
            default={}, 
            sa_column=Column(JSON().with_variant(JSONB, "postgresql"), nullable=False)
        )
    scanned_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
