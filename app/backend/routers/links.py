from fastapi import APIRouter, Depends, Response, status, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List

from app.backend.database.database import get_db
from app.backend.models.models import User
from app.backend.schemas.schemas import LinkCreate, Link as LinkSchema, LinkStats
from app.backend.services.deps import get_current_user
from app.backend.services.link_service import LinkService

router = APIRouter(tags=["links"])


@router.post("/links/shorten", response_model=LinkSchema)
def create_short_link(
    link: LinkCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    link_service = LinkService(db)
    return link_service.create_short_link(
        original_url=str(link.original_url),
        current_user=current_user,
        custom_alias=link.custom_alias,
        expires_at=link.expires_at
    )


@router.get("/search", response_model=List[LinkSchema])
def search_links(original_url: str, db: Session = Depends(get_db)):
    link_service = LinkService(db)
    return link_service.search_links(original_url)


@router.get("/links/user", response_model=List[LinkSchema])
def get_user_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    link_service = LinkService(db)
    return link_service.get_user_links(current_user)


@router.get("/links/{short_code}", response_model=LinkSchema)
def get_link_info(short_code: str, db: Session = Depends(get_db)):
    link_service = LinkService(db)
    return link_service.get_link_by_code(short_code)


@router.delete("/links/{short_code}")
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    link_service = LinkService(db)
    link_service.delete_link(short_code, current_user)
    return {"message": "Link deleted successfully"}


@router.put("/links/{short_code}", response_model=LinkSchema)
def update_link(
    short_code: str,
    link: LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    link_service = LinkService(db)
    return link_service.update_link(
        short_code=short_code,
        current_user=current_user,
        original_url=str(link.original_url),
        expires_at=link.expires_at,
        custom_alias=link.custom_alias
    )


@router.get("/links/{short_code}/stats", response_model=LinkStats)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    link_service = LinkService(db)
    return link_service.get_link_by_code(short_code)


@router.get("/{short_code}", response_class=Response)
def redirect_to_url(short_code: str, db: Session = Depends(get_db)):
    try:
        link_service = LinkService(db)
        link = link_service.get_link_by_code(short_code)
        link_service.check_link_expiration(link)
        link_service.update_link_stats(link)

        return Response(
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
            headers={"Location": link.original_url}
        )
    except HTTPException as e:
        if e.status_code == status.HTTP_404_NOT_FOUND:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Short link not found"
            )
        raise e
