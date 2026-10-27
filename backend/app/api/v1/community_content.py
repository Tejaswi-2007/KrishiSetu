"""Community groups/posts and source-linked government schemes/news."""
from datetime import datetime, timezone, timedelta
from typing import Literal
from xml.etree import ElementTree
from email.utils import parsedate_to_datetime

import httpx
from pydantic import BaseModel, Field, HttpUrl, model_validator
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import desc, or_

from app.core.database import get_db
from app.core.security import get_current_user, require_role
from app.models.user import User
from app.models.community_content import CommunityGroup, CommunityMembership, CommunityPost, PublicResource

router = APIRouter()
_last_news_sync: datetime | None = None

CROP_GROUPS = ["Cotton", "Papaya", "Banana", "Jowar", "Wheat", "Bajra", "Fruits", "Vegetables"]

class CommunityCreate(BaseModel):
    kind: Literal["crop", "region"]
    name: str = Field(min_length=2, max_length=180)
    crop: str | None = Field(default=None, max_length=80)
    state: str | None = Field(default=None, max_length=120)
    district: str | None = Field(default=None, max_length=120)
    taluka: str | None = Field(default=None, max_length=120)
    village: str | None = Field(default=None, max_length=120)

    @model_validator(mode="after")
    def validate_group(self):
        if self.kind == "crop" and not self.crop:
            raise ValueError("Crop community requires a crop name")
        if self.kind == "region" and not any([self.state, self.district, self.taluka, self.village]):
            raise ValueError("Provide at least a state, district, taluka, or village")
        return self

class PostCreate(BaseModel):
    body: str = Field(min_length=2, max_length=5000)
    category: str = Field(default="General", min_length=2, max_length=80)
    community_id: int | None = None

class ResourceCreate(BaseModel):
    kind: Literal["scheme", "news"]
    title: str = Field(min_length=3, max_length=300)
    summary: str = Field(min_length=5, max_length=10000)
    documents: str | None = Field(default=None, max_length=5000)
    source_name: str = Field(min_length=2, max_length=200)
    source_url: HttpUrl
    published_at: datetime | None = None

def group_dict(g: CommunityGroup, db: Session):
    return {"id": g.id, "name": g.name, "kind": g.kind, "crop": g.crop, "state": g.state, "district": g.district, "taluka": g.taluka, "village": g.village, "created_at": g.created_at.isoformat(), "member_count": db.query(CommunityMembership).filter(CommunityMembership.community_id == g.id).count(), "post_count": db.query(CommunityPost).filter(CommunityPost.community_id == g.id).count()}

def post_dict(p: CommunityPost, db: Session):
    author = db.query(User).filter(User.id == p.author_id).first()
    group = db.query(CommunityGroup).filter(CommunityGroup.id == p.community_id).first() if p.community_id else None
    return {"id": p.id, "author_id": p.author_id, "author_name": author.full_name if author else "Former user", "body": p.body, "category": p.category, "community_id": p.community_id, "community_name": group.name if group else None, "created_at": p.created_at.isoformat()}

def resource_dict(r: PublicResource):
    return {"id": r.id, "kind": r.kind, "title": r.title, "summary": r.summary, "documents": r.documents, "source_name": r.source_name, "source_url": r.source_url, "published_at": r.published_at.isoformat() if r.published_at else None}

@router.get("/community/groups")
def list_groups(kind: Literal["crop", "region"] | None = None, q: str | None = None, db: Session = Depends(get_db)):
    query = db.query(CommunityGroup)
    if kind: query = query.filter(CommunityGroup.kind == kind)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(CommunityGroup.name.ilike(term), CommunityGroup.crop.ilike(term), CommunityGroup.state.ilike(term), CommunityGroup.district.ilike(term), CommunityGroup.taluka.ilike(term), CommunityGroup.village.ilike(term)))
    groups = query.order_by(CommunityGroup.kind, CommunityGroup.name).all()
    return {"items": [group_dict(g, db) for g in groups], "total": len(groups), "crop_options": CROP_GROUPS}

@router.post("/community/groups", status_code=status.HTTP_201_CREATED)
def create_group(data: CommunityCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    name = data.name.strip()
    filters = [CommunityGroup.kind == data.kind, CommunityGroup.name.ilike(name)]
    for key in ("crop", "state", "district", "taluka", "village"):
        value = getattr(data, key)
        filters.append(getattr(CommunityGroup, key).is_(None) if not value else getattr(CommunityGroup, key).ilike(value.strip()))
    existing = db.query(CommunityGroup).filter(*filters).first()
    if existing:
        return group_dict(existing, db)
    group = CommunityGroup(kind=data.kind, name=name, crop=data.crop.strip() if data.crop else None, state=data.state.strip() if data.state else None, district=data.district.strip() if data.district else None, taluka=data.taluka.strip() if data.taluka else None, village=data.village.strip() if data.village else None, created_by=current_user.id)
    db.add(group); db.flush()
    db.add(CommunityMembership(community_id=group.id, user_id=current_user.id))
    db.commit(); db.refresh(group)
    return group_dict(group, db)

@router.post("/community/groups/{group_id}/join")
def join_group(group_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    group = db.query(CommunityGroup).filter(CommunityGroup.id == group_id).first()
    if not group: raise HTTPException(status_code=404, detail="Community not found")
    membership = db.query(CommunityMembership).filter_by(community_id=group_id, user_id=current_user.id).first()
    if not membership:
        db.add(CommunityMembership(community_id=group_id, user_id=current_user.id)); db.commit()
    return {"joined": True, "community_id": group_id}

@router.get("/community/posts")
def list_posts(community_id: int | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(CommunityPost)
    if community_id is not None: query = query.filter(CommunityPost.community_id == community_id)
    total = query.count()
    posts = query.order_by(desc(CommunityPost.created_at)).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [post_dict(p, db) for p in posts], "total": total, "page": page, "page_size": page_size}

@router.post("/community/posts", status_code=status.HTTP_201_CREATED)
def create_post(data: PostCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if data.community_id is not None:
        group = db.query(CommunityGroup).filter(CommunityGroup.id == data.community_id).first()
        if not group: raise HTTPException(status_code=404, detail="Community not found")
        membership = db.query(CommunityMembership).filter_by(community_id=group.id, user_id=current_user.id).first()
        if not membership:
            db.add(CommunityMembership(community_id=group.id, user_id=current_user.id))
    post = CommunityPost(author_id=current_user.id, community_id=data.community_id, body=data.body.strip(), category=data.category.strip())
    db.add(post); db.commit(); db.refresh(post)
    return post_dict(post, db)

@router.delete("/community/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
    if not post: raise HTTPException(status_code=404, detail="Post not found")
    if post.author_id != current_user.id and current_user.role.value != "admin": raise HTTPException(status_code=403, detail="You can delete only your own posts")
    db.delete(post); db.commit()

AGRICULTURE_KEYWORDS = ("agriculture", "farmer", "farmers", "crop", "kisan", "fertilizer", "fertiliser", "irrigation", "wheat", "rice", "cotton", "horticulture", "pm-kisan", "minimum support price", "mandi", "livestock", "agri")
PIB_RSS_URL = "https://pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=5"

def _sync_pib_news(db: Session):
    global _last_news_sync
    now = datetime.now(timezone.utc)
    if _last_news_sync and now - _last_news_sync < timedelta(minutes=30): return {"synced": 0, "cached": True}
    try:
        response = httpx.get(PIB_RSS_URL, timeout=12.0, headers={"User-Agent": "KrishiSetu/1.0 (+official agriculture news reader)"})
        response.raise_for_status()
        root = ElementTree.fromstring(response.content)
    except (httpx.HTTPError, ElementTree.ParseError) as exc:
        # Don't erase previously saved records when the official feed is unavailable.
        raise HTTPException(status_code=502, detail=f"Official PIB RSS feed is temporarily unavailable: {exc}") from exc
    saved = 0
    for item in root.findall(".//item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        haystack = f"{title} {description}".lower()
        if not title or not link or not any(k in haystack for k in AGRICULTURE_KEYWORDS): continue
        if db.query(PublicResource).filter(PublicResource.kind == "news", PublicResource.source_url == link).first(): continue
        published = None
        raw_date = (item.findtext("pubDate") or "").strip()
        if raw_date:
            try: published = parsedate_to_datetime(raw_date)
            except (TypeError, ValueError, OverflowError): pass
        clean_summary = " ".join(description.split())
        if not clean_summary: clean_summary = "Official PIB agriculture-related update. Open the original source for the complete announcement."
        db.add(PublicResource(kind="news", title=title[:300], summary=clean_summary[:10000], source_name="Press Information Bureau (Government of India)", source_url=link, published_at=published))
        saved += 1
    db.commit(); _last_news_sync = now
    return {"synced": saved, "cached": False}

@router.get("/resources/{kind}")
def list_resources(kind: Literal["scheme", "news"], q: str | None = None, page: int = Query(1, ge=1), page_size: int = Query(30, ge=1, le=100), refresh: bool = False, db: Session = Depends(get_db)):
    sync_status = None
    if kind == "news" and refresh:
        try: sync_status = _sync_pib_news(db)
        except HTTPException:
            # Return cached DB news with a source status note rather than failing the whole page.
            sync_status = {"warning": "Live PIB feed could not be refreshed; showing saved articles."}
    query = db.query(PublicResource).filter(PublicResource.kind == kind)
    if q:
        term = f"%{q.strip()}%"
        query = query.filter(or_(PublicResource.title.ilike(term), PublicResource.summary.ilike(term)))
    total = query.count()
    rows = query.order_by(desc(PublicResource.published_at), desc(PublicResource.created_at)).offset((page-1)*page_size).limit(page_size).all()
    return {"items": [resource_dict(r) for r in rows], "total": total, "page": page, "page_size": page_size, "sync_status": sync_status, "note": "Records are source-linked and persisted in PostgreSQL."}

@router.post("/resources", status_code=status.HTTP_201_CREATED)
def create_resource(data: ResourceCreate, current_user: User = Depends(require_role("admin")), db: Session = Depends(get_db)):
    row = PublicResource(kind=data.kind, title=data.title.strip(), summary=data.summary.strip(), documents=data.documents.strip() if data.documents else None, source_name=data.source_name.strip(), source_url=str(data.source_url), published_at=data.published_at, created_by=current_user.id)
    db.add(row); db.commit(); db.refresh(row)
    return resource_dict(row)
