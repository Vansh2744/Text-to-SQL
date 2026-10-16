from fastapi import APIRouter, Depends, Query
from sqlalchemy import delete, select, update
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_llm, get_owned, get_ready_dataset
from app.core.config import Settings, get_settings
from app.core.ratelimit import limiter
from app.db.session import get_db
from app.models import Conversation, Message, QueryHistory, User
from app.schemas import (
    AnalysisOut,
    ConversationDetail,
    ConversationIn,
    ConversationOut,
    MessageRequest,
)
from app.services.llm_service import LLMProvider
from app.services.query_service import analyze_question

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationOut, status_code=201)
def create(body: ConversationIn, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    ds = get_ready_dataset(db, body.dataset_id, user)
    conv = Conversation(owner_id=user.id, dataset_id=ds.id, title=body.title or "New conversation")
    db.add(conv)
    db.commit()
    return conv


@router.get("", response_model=list[ConversationOut])
def list_conversations(limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0),
                       db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    q = select(Conversation).where(Conversation.owner_id == user.id)
    return db.scalars(q.order_by(Conversation.updated_at.desc()).limit(limit).offset(offset)).all()


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str, db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    conv = get_owned(db, Conversation, conversation_id, user)
    msgs = db.scalars(select(Message).where(Message.conversation_id == conv.id)
                      .order_by(Message.created_at)).all()
    return {**ConversationOut.model_validate(conv).model_dump(), "messages": msgs}


@router.post("/{conversation_id}/messages", response_model=AnalysisOut)
def post_message(conversation_id: str, body: MessageRequest, db: Session = Depends(get_db),
                 user: User = Depends(get_current_user), provider: LLMProvider = Depends(get_llm),
                 settings: Settings = Depends(get_settings)):
    limiter.check(user.id)
    conv = get_owned(db, Conversation, conversation_id, user)
    ds = get_ready_dataset(db, conv.dataset_id, user)
    return analyze_question(db, user, ds, body.question, provider, settings, conv)


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str, db: Session = Depends(get_db),
                        user: User = Depends(get_current_user)):
    conv = get_owned(db, Conversation, conversation_id, user)
    db.execute(delete(Message).where(Message.conversation_id == conv.id))
    db.execute(update(QueryHistory).where(QueryHistory.conversation_id == conv.id)
               .values(conversation_id=None))
    db.delete(conv)
    db.commit()
