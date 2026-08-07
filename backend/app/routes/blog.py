"""
Professional AI - Blog Routes
Public blog posts for the knowledge hub.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.models.blog import BlogPost
from app.services.auth_service import get_current_admin, get_current_user
from loguru import logger

router = APIRouter(prefix="/api/blog", tags=["Blog"])


class BlogPostCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    slug: str = Field(..., min_length=1, max_length=500)
    excerpt: Optional[str] = Field(default=None, max_length=2000)
    content: str = Field(..., min_length=1)
    cover_gradient: Optional[str] = Field(default=None, max_length=255)
    author: Optional[str] = Field(default=None, max_length=255)
    date: Optional[str] = Field(default=None, max_length=255)
    read_time: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = Field(default=None)
    published: bool = Field(default=True)


class BlogPostUpdate(BaseModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=500)
    slug: Optional[str] = Field(default=None, min_length=1, max_length=500)
    excerpt: Optional[str] = Field(default=None, max_length=2000)
    content: Optional[str] = Field(default=None, min_length=1)
    cover_gradient: Optional[str] = Field(default=None, max_length=255)
    author: Optional[str] = Field(default=None, max_length=255)
    date: Optional[str] = Field(default=None, max_length=255)
    read_time: Optional[str] = Field(default=None, max_length=50)
    category: Optional[str] = Field(default=None, max_length=100)
    tags: Optional[List[str]] = Field(default=None)
    published: Optional[bool] = Field(default=None)


class BlogPostResponse(BaseModel):
    id: str
    title: str
    slug: str
    excerpt: Optional[str]
    content: str
    cover_gradient: Optional[str]
    author: Optional[str]
    date: Optional[str]
    read_time: Optional[str]
    category: Optional[str]
    tags: Optional[List[str]]
    published: bool
    created_at: Optional[str]
    updated_at: Optional[str]


def _post_to_dict(post) -> Dict[str, Any]:
    return {
        "id": str(post.id),
        "title": post.title,
        "slug": post.slug,
        "excerpt": post.excerpt,
        "content": post.content,
        "cover_gradient": post.cover_gradient,
        "author": post.author,
        "date": post.date,
        "read_time": post.read_time,
        "category": post.category,
        "tags": post.tags or [],
        "published": post.published,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@router.get("/posts", response_model=List[BlogPostResponse])
async def list_posts(
    category: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    query = select(BlogPost).where(BlogPost.published == True).order_by(desc(BlogPost.created_at)).limit(limit)
    if category:
        query = query.where(BlogPost.category == category)
    result = await db.execute(query)
    posts = result.scalars().all()
    return [_post_to_dict(p) for p in posts]


@router.get("/posts/{slug}", response_model=BlogPostResponse)
async def get_post(slug: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost).where(BlogPost.slug == slug))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    if not post.published:
        raise HTTPException(status_code=404, detail="Post not found")
    return _post_to_dict(post)


@router.get("/categories", response_model=List[str])
async def list_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost.category).where(BlogPost.published == True, BlogPost.category.is_not(None)).distinct())
    categories = [row[0] for row in result.all() if row[0]]
    return sorted(categories)


@router.post("/posts", response_model=BlogPostResponse)
async def create_post(data: BlogPostCreate, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    existing = await db.execute(select(BlogPost).where(BlogPost.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Slug already exists")

    post = BlogPost(
        title=data.title,
        slug=data.slug,
        excerpt=data.excerpt,
        content=data.content,
        cover_gradient=data.cover_gradient,
        author=data.author,
        date=data.date,
        read_time=data.read_time,
        category=data.category,
        tags=data.tags or [],
        published=data.published,
        created_by=uuid.UUID(str(current_user.id)) if current_user else None,
    )
    db.add(post)
    await db.commit()
    await db.refresh(post)
    logger.info(f"Blog post created: {post.slug} by user {current_user.id}")
    return _post_to_dict(post)


@router.put("/posts/{post_id}", response_model=BlogPostResponse)
async def update_post(post_id: str, data: BlogPostUpdate, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = data.model_dump(exclude_unset=True)
    if "slug" in update_data:
        existing = await db.execute(select(BlogPost).where(BlogPost.slug == update_data["slug"], BlogPost.id != post_id))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Slug already exists")

    for field, value in update_data.items():
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post)
    logger.info(f"Blog post updated: {post.slug} by user {current_user.id}")
    return _post_to_dict(post)


@router.delete("/posts/{post_id}")
async def delete_post(post_id: str, current_user = Depends(get_current_admin), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlogPost).where(BlogPost.id == post_id))
    post = result.scalar_one_or_none()
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    await db.delete(post)
    await db.commit()
    logger.info(f"Blog post deleted: {post.slug} by user {current_user.id}")
    return {"message": "Post deleted successfully"}
