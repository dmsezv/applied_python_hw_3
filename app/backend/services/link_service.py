from datetime import datetime, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import secrets
import string
from zoneinfo import ZoneInfo

from app.backend.models.models import Link, User


class LinkService:
    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def generate_short_code(length: int = 6) -> str:
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def create_short_link(
        self,
        original_url: str,
        current_user: Optional[User] = None,
        custom_alias: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> Link:
        if expires_at:
            expires_at = expires_at.replace(tzinfo=ZoneInfo("UTC"))
            if expires_at < datetime.now(ZoneInfo("UTC")):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Expiration date must be in the future"
                )
        else:
            # if user is not authenticated, set expires_at to 1 day
            expires_at = datetime.now(ZoneInfo("UTC")) + timedelta(days=1)

        if custom_alias:
            if self.db.query(Link).filter(Link.short_code == custom_alias).first():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Custom alias already in use"
                )
            short_code = custom_alias
        else:
            while True:
                short_code = self.generate_short_code()
                if not self.db.query(Link).filter(Link.short_code == short_code).first():
                    break

        db_link = Link(
            original_url=original_url,
            short_code=short_code,
            user_id=current_user.id if current_user else None,
            expires_at=expires_at
        )
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def get_link_by_code(self, short_code: str) -> Link:
        link = self.db.query(Link).filter(Link.short_code == short_code).first()
        if not link:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Link not found"
            )
        return link

    def update_link_stats(self, link: Link) -> Link:
        link.clicks += 1
        link.last_accessed_at = datetime.now(ZoneInfo("UTC"))
        self.db.commit()
        self.db.refresh(link)
        return link

    def check_link_expiration(self, link: Link) -> None:
        if link.expires_at and link.expires_at < datetime.now(ZoneInfo("UTC")):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail="Link has expired"
            )

    def delete_link(self, short_code: str, current_user: User) -> None:
        link = self.get_link_by_code(short_code)

        if link.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to delete this link"
            )

        self.db.delete(link)
        self.db.commit()

    def update_link(
        self,
        short_code: str,
        current_user: User,
        original_url: str,
        expires_at: Optional[datetime] = None
    ) -> Link:
        link = self.get_link_by_code(short_code)
        
        if link.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to update this link"
            )

        link.original_url = original_url
        link.expires_at = expires_at.replace(tzinfo=ZoneInfo("UTC")) if expires_at else None
        self.db.commit()
        self.db.refresh(link)
        return link

    def search_links(self, original_url: str) -> List[Link]:
        return self.db.query(Link).filter(
            Link.original_url.contains(original_url)
        ).all()

    def get_user_links(self, current_user: User) -> List[Link]:
        return self.db.query(Link).filter(
            Link.user_id == current_user.id
        ).all()
