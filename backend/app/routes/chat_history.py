"""
Professional AI - Chat History Routes
Conversation management, message history, search, rename, delete.
SECURITY HARDENED: RLS, input validation, rate limiting.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import JSONResponse
from sqlalchemy import select, and_, desc, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
import uuid
from datetime import datetime, timezone

from app.database import get_db
from app.config import settings
from app.models.user import User
from app.models.chat_history import Conversation, Message
from app.models.usage import UsageLog
from app.services.auth_service import AuthService, get_current_user
from app.services.ai_service import ai_service
from app.services.ai_router import ModelType
from app.routes.chat import SYSTEM_PROMPTS
from app.middleware.security import InputSanitizer, limiter

router = APIRouter(prefix="/api/conversations", tags=["Chat History"])


# ===================================================================
# PYDANTIC SCHEMAS
# ===================================================================

class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=255)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v):
        if v is None:
            return v
        return InputSanitizer.sanitize_text(v, max_length=255)


class ConversationRename(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

    @field_validator("title", mode="before")
    @classmethod
    def sanitize_title(cls, v):
        return InputSanitizer.sanitize_text(v, max_length=255)


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=100_000)
    mode: str = Field(default="chat", pattern="^(chat|code|security|bugfix)$")
    role: str = Field(default="user", pattern="^(user|assistant)$")

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v):
        return InputSanitizer.sanitize_text(v, max_length=100_000)


class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    mode: str
    created_at: str

    @classmethod
    def from_message(cls, message: Message):
        return cls(
            id=str(message.id),
            role=message.role,
            content=message.content,
            mode=message.mode,
            created_at=message.created_at.isoformat() if message.created_at else datetime.now(timezone.utc).isoformat(),
        )


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int

    @classmethod
    def from_conversation(cls, conv: Conversation):
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(conv.id),
            title=conv.title or "Untitled",
            created_at=conv.created_at.isoformat() if conv.created_at else now,
            updated_at=conv.updated_at.isoformat() if conv.updated_at else now,
            message_count=len(conv.messages) if hasattr(conv, 'messages') and conv.messages is not None else 0,
        )


class ConversationDetail(ConversationResponse):
    messages: List[MessageResponse]

    @classmethod
    def from_conversation_detail(cls, conv: Conversation):
        now = datetime.now(timezone.utc).isoformat()
        return cls(
            id=str(conv.id),
            title=conv.title or "Untitled",
            created_at=conv.created_at.isoformat() if conv.created_at else now,
            updated_at=conv.updated_at.isoformat() if conv.updated_at else now,
            message_count=len(conv.messages) if hasattr(conv, 'messages') and conv.messages is not None else 0,
            messages=[MessageResponse.from_message(msg) for msg in sorted(conv.messages, key=lambda m: m.created_at or datetime.min.replace(tzinfo=timezone.utc))] if hasattr(conv, 'messages') and conv.messages else [],
        )


# ===================================================================
# HELPER FUNCTIONS
# ===================================================================

def _error_response(exc: Exception, status_code: int = 500, message: str | None = None):
    """Return a clean JSON error response."""
    from fastapi.responses import JSONResponse
    logger = __import__("loguru").logger
    logger.error(f"Chat history endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status_code,
        content={
            "detail": message or f"Internal error: {exc}",
            "error": "chat_history_request_failed",
        },
    )


def _generate_title_from_prompt(prompt: str, max_length: int = 40) -> str:
    """Generate a short title from the first user message."""
    # Clean and truncate
    title = prompt.strip().replace('\n', ' ')
    if len(title) > max_length:
        title = title[:max_length].rsplit(' ', 1)[0] + '...'
    return title or "New Conversation"


def _format_relative_date(date: datetime) -> str:
    """Format date as relative string: Today, Yesterday, or date."""
    now = datetime.now(timezone.utc)
    diff = now - date
    
    if diff.days == 0:
        return "Today"
    elif diff.days == 1:
        return "Yesterday"
    elif diff.days < 7:
        return f"{diff.days} days ago"
    else:
        return date.strftime("%d %b")


# ===================================================================
# ROUTES
# ===================================================================

@router.get("", response_model=List[ConversationResponse])
@limiter.limit("100/minute")
async def list_conversations(
    request: Request,
    search: Optional[str] = Query(None, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all conversations for the current user.
    Optional search by title.
    """
    try:
        query = select(Conversation).where(Conversation.user_id == current_user.id)
        
        # Search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(Conversation.title.ilike(search_term))
        
        # Order by most recently updated
        query = query.order_by(desc(Conversation.updated_at))
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Get message counts
        conv_list = []
        for conv in conversations:
            msg_count_query = select(func.count(Message.id)).where(Message.conversation_id == conv.id)
            msg_count_result = await db.execute(msg_count_query)
            msg_count = msg_count_result.scalar_one_or_none() or 0
            
            conv_data = ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                created_at=conv.created_at.isoformat(),
                updated_at=conv.updated_at.isoformat(),
                message_count=msg_count,
            )
            conv_list.append(conv_data)
        
        return conv_list
    except HTTPException:
        raise
    except Exception as exc:
        return _error_response(exc, message="Failed to load conversations")


@router.get("/{conversation_id}", response_model=ConversationDetail)
@limiter.limit("100/minute")
async def get_conversation(
    request: Request,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full conversation with all messages.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        query = select(Conversation).options(selectinload(Conversation.messages)).where(
            and_(
                Conversation.id == conv_uuid,
                Conversation.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        return ConversationDetail.from_conversation_detail(conversation)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )
    except Exception as exc:
        return _error_response(exc, message="Failed to load conversation")


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("50/minute")
async def create_conversation(
    request: Request,
    data: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation.
    """
    try:
        title = data.title or "New Conversation"
        
        conversation = Conversation(
            user_id=current_user.id,
            title=title,
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            message_count=0,
        )
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to create conversation")


@router.post("/{conversation_id}/messages", response_model=MessageResponse)
@limiter.limit("50/minute")
async def add_message(
    request: Request,
    conversation_id: str,
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a message to a conversation.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        # Verify conversation exists and belongs to user
        conv_query = select(Conversation).where(
            and_(
                Conversation.id == conv_uuid,
                Conversation.user_id == current_user.id,
            )
        )
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        # Create message
        message = Message(
            conversation_id=conv_uuid,
            role=message_data.role,
            content=message_data.content,
            mode=message_data.mode,
        )
        db.add(message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(message)
        
        return MessageResponse.from_message(message)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to add message")


@router.patch("/{conversation_id}", response_model=ConversationResponse)
@limiter.limit("50/minute")
async def rename_conversation(
    request: Request,
    conversation_id: str,
    data: ConversationRename,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rename a conversation.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        query = select(Conversation).where(
            and_(
                Conversation.id == conv_uuid,
                Conversation.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        conversation.title = data.title
        await db.commit()
        await db.refresh(conversation)

        msg_count_query = select(func.count(Message.id)).where(Message.conversation_id == conv_uuid)
        msg_count_result = await db.execute(msg_count_query)
        msg_count = msg_count_result.scalar_one_or_none() or 0

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            created_at=conversation.created_at.isoformat(),
            updated_at=conversation.updated_at.isoformat(),
            message_count=msg_count,
        )
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to rename conversation")


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def delete_conversation(
    request: Request,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation and all its messages.
    """
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        query = select(Conversation).where(
            and_(
                Conversation.id == conv_uuid,
                Conversation.user_id == current_user.id,
            )
        )
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        await db.delete(conversation)
        await db.commit()
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to delete conversation")


# ===================================================================
# ADMIN ROUTES (Owner can view all conversations)
# ===================================================================

@router.get("/admin/all", response_model=List[dict])
@limiter.limit("100/minute")
async def admin_list_all_conversations(
    request: Request,
    search: Optional[str] = Query(None, max_length=255),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin/Owner: List all conversations across all users.
    """
    # Check if user is admin
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    try:
        # Join with users to get email
        from sqlalchemy.orm import joinedload
        query = select(Conversation).options(joinedload(Conversation.user))
        
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(Conversation.title.ilike(search_term))
        
        query = query.order_by(desc(Conversation.updated_at))
        
        result = await db.execute(query)
        conversations = result.unique().scalars().all()
        
        # Format with user info
        conv_list = []
        for conv in conversations:
            msg_count_query = select(func.count(Message.id)).where(Message.conversation_id == conv.id)
            msg_count_result = await db.execute(msg_count_query)
            msg_count = msg_count_result.scalar_one_or_none() or 0
            
            conv_list.append({
                "id": str(conv.id),
                "title": conv.title,
                "user_id": str(conv.user_id),
                "user_email": conv.user.email if conv.user else "Unknown",
                "created_at": conv.created_at.isoformat(),
                "updated_at": conv.updated_at.isoformat(),
                "message_count": msg_count,
            })
        
        return conv_list
    except HTTPException:
        raise
    except Exception as exc:
        return _error_response(exc, message="Failed to load conversations")


@router.delete("/admin/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("50/minute")
async def admin_delete_conversation(
    request: Request,
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Admin/Owner: Delete any conversation.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    
    try:
        conv_uuid = uuid.UUID(conversation_id)
        
        query = select(Conversation).where(Conversation.id == conv_uuid)
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found",
            )
        
        await db.delete(conversation)
        await db.commit()
        
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content={})
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid conversation ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to delete conversation")


# ===================================================================
# MESSAGE EDIT & REGENERATE ROUTES
# ===================================================================

class MessageEdit(BaseModel):
    content: str = Field(..., min_length=1, max_length=100_000)

    @field_validator("content", mode="before")
    @classmethod
    def sanitize_content(cls, v):
        return InputSanitizer.sanitize_text(v, max_length=100_000)


class MessageFeedback(BaseModel):
    feedback: str = Field(..., pattern="^(thumbs_up|thumbs_down)$")


class MessageEditResponse(BaseModel):
    id: str
    role: str
    content: str
    mode: str
    is_edited: bool
    updated_at: str

    @classmethod
    def from_message(cls, message: Message):
        return cls(
            id=str(message.id),
            role=message.role,
            content=message.content,
            mode=message.mode,
            is_edited=message.is_edited if hasattr(message, 'is_edited') else False,
            updated_at=message.updated_at.isoformat() if hasattr(message, 'updated_at') and message.updated_at else message.created_at.isoformat() if hasattr(message, 'created_at') and message.created_at else datetime.now(timezone.utc).isoformat(),
        )


@router.patch("/messages/{message_id}", response_model=MessageEditResponse)
@limiter.limit("30/minute")
async def edit_message(
    request: Request,
    message_id: str,
    edit_data: MessageEdit,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Edit a user message and return updated message.
    The frontend will handle re-generating the AI response.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
        
        # Get message with conversation
        query = select(Message).where(Message.id == msg_uuid)
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        # Verify the message belongs to the user's conversation
        conv_query = select(Conversation).where(
            and_(
                Conversation.id == message.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        
        # Only allow editing user messages
        if message.role != 'user':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only user messages can be edited",
            )
        
        # Update message
        message.content = edit_data.content
        message.is_edited = True
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(message)
        
        return MessageEditResponse.from_message(message)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to edit message")


@router.post("/messages/{message_id}/regenerate", response_model=MessageResponse)
@limiter.limit("20/minute")
async def regenerate_response(
    request: Request,
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Regenerate AI response for a user message.
    Finds the user message, gets the next assistant message, and replaces it with a new response.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
        
        # Get the user message
        query = select(Message).where(Message.id == msg_uuid)
        result = await db.execute(query)
        user_message = result.scalar_one_or_none()
        
        if not user_message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        # Verify the message belongs to the user's conversation
        conv_query = select(Conversation).where(
            and_(
                Conversation.id == user_message.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        
        # Only allow regenerating for user messages
        if user_message.role != 'user':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only user messages can be regenerated",
            )
        
        # Find the next assistant message (the one to replace)
        next_msg_query = select(Message).where(
            and_(
                Message.conversation_id == user_message.conversation_id,
                Message.role == 'assistant',
                Message.created_at > user_message.created_at,
            )
        ).order_by(Message.created_at.asc()).limit(1)
        
        next_msg_result = await db.execute(next_msg_query)
        assistant_message = next_msg_result.scalar_one_or_none()
        
        # Generate new AI response
        system_prompt = SYSTEM_PROMPTS.get(user_message.mode, SYSTEM_PROMPTS["chat"])
        
        ai_result = await ai_service.generate(
            prompt=user_message.content,
            system_prompt=system_prompt,
            model=None,
            model_type=ModelType.CHAT,
        )
        
        # Update or create assistant message
        if assistant_message:
            # Replace existing response
            assistant_message.content = ai_result.content
            assistant_message.is_edited = True
        else:
            # Create new assistant message if none exists
            assistant_message = Message(
                conversation_id=user_message.conversation_id,
                role='assistant',
                content=ai_result.content,
                mode=user_message.mode,
                is_edited=True,
            )
            db.add(assistant_message)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now(timezone.utc)
        
        # Log usage
        usage_log = UsageLog(
            user_id=current_user.id,
            action=f"{user_message.mode}_regeneration" if user_message.mode != 'chat' else "chat_regeneration",
            tokens_used=ai_result.tokens,
            prompt_text=user_message.content[:500],
            response_text=ai_result.content[:500],
            model_used=ai_result.model,
            execution_time_ms=ai_result.execution_time_ms,
        )
        db.add(usage_log)
        
        await db.commit()
        await db.refresh(assistant_message)
        
        return MessageResponse.from_message(assistant_message)
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to regenerate response")


@router.patch("/messages/{message_id}/feedback")
@limiter.limit("50/minute")
async def set_message_feedback(
    request: Request,
    message_id: str,
    feedback_data: MessageFeedback,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Set feedback (thumbs_up/thumbs_down) on a message.
    """
    try:
        msg_uuid = uuid.UUID(message_id)
        
        # Get message with conversation
        query = select(Message).where(Message.id == msg_uuid)
        result = await db.execute(query)
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found",
            )
        
        # Verify the message belongs to the user's conversation
        conv_query = select(Conversation).where(
            and_(
                Conversation.id == message.conversation_id,
                Conversation.user_id == current_user.id,
            )
        )
        conv_result = await db.execute(conv_query)
        conversation = conv_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied",
            )
        
        # Only allow feedback on assistant messages
        if message.role != 'assistant':
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only assistant messages can receive feedback",
            )
        
        # Update feedback
        message.feedback = feedback_data.feedback
        message.feedback_updated_at = datetime.now(timezone.utc)
        
        # Update conversation timestamp
        conversation.updated_at = datetime.now(timezone.utc)
        
        await db.commit()
        await db.refresh(message)

        feedback_updated_at = message.feedback_updated_at.isoformat() if message.feedback_updated_at else None

        return JSONResponse(content={
            "id": str(message.id),
            "feedback": message.feedback,
            "feedback_updated_at": feedback_updated_at,
        })
    except HTTPException:
        raise
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid message ID",
        )
    except Exception as exc:
        await db.rollback()
        return _error_response(exc, message="Failed to set feedback")
