from sqlalchemy.orm import Session

from app.models.advisory import Advisory
from app.models.ingested_source import IngestedSource
from app.models.user import User
from app.models.watchlist import Watchlist
from app.vectorstore.qdrant_client import collection_name_for


def test_watchlist_query_scoped_by_user_id_only_sees_own_rows(db: Session, two_users: tuple[User, User]) -> None:
    user_a, user_b = two_users
    assert db.query(Watchlist).filter(Watchlist.user_id == user_a.id).count() == 1
    assert db.query(Watchlist).filter(Watchlist.user_id == user_b.id).count() == 0


def test_advisory_query_scoped_by_user_id_only_sees_own_rows(db: Session, two_users: tuple[User, User]) -> None:
    user_a, user_b = two_users
    assert db.query(Advisory).filter(Advisory.user_id == user_a.id).count() == 1
    assert db.query(Advisory).filter(Advisory.user_id == user_b.id).count() == 0


def test_ingested_source_query_scoped_by_user_id_only_sees_own_rows(db: Session, two_users: tuple[User, User]) -> None:
    user_a, user_b = two_users
    assert db.query(IngestedSource).filter(IngestedSource.user_id == user_a.id).count() == 1
    assert db.query(IngestedSource).filter(IngestedSource.user_id == user_b.id).count() == 0


def test_qdrant_collection_names_never_collide_across_tenants(two_users: tuple[User, User]) -> None:
    user_a, user_b = two_users
    assert collection_name_for(user_a.id) != collection_name_for(user_b.id)
    assert collection_name_for(user_a.id) == f"kb_{user_a.id}"
