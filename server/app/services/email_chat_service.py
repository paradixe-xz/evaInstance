"""Email chat service orchestrating inbound/outbound email handling."""
from __future__ import annotations

from typing import Any, Dict, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.logging import get_logger
from ..models.chat import MessageDirection, MessageType
from ..repositories.user_repository import UserRepository
from ..repositories.chat_repository import ChatRepository, MessageRepository
from .ollama_service import OllamaService
from .email_service import EmailService

logger = get_logger(__name__)


class EmailChatService:
    """Service to process email conversations."""

    def __init__(self) -> None:
        self.ollama_service = OllamaService()
        self.email_service = EmailService()

    def persist_outgoing_email(self, request, provider_response: Dict[str, Any]) -> Dict[str, Any]:
        """Persist outgoing email message in the database."""
        with get_db() as db:
            user_repo = UserRepository(db)
            chat_repo = ChatRepository(db)
            message_repo = MessageRepository(db)

            user = user_repo.get_by_email(request.to)
            if not user:
                user = user_repo.create_email_user(email=request.to, name=None)

            session = chat_repo.get_active_session_for_user(user.id, channel="email")
            if not session:
                session_id = f"email_{user.id}_{int(datetime.utcnow().timestamp())}"
                session = chat_repo.create_session(
                    user_id=user.id,
                    session_id=session_id,
                    channel="email",
                    ai_personality="ana",
                )

            message = message_repo.create_message(
                user_id=user.id,
                chat_session_id=session.id,
                content=request.text or request.html or "",
                subject=request.subject,
                direction=MessageDirection.OUTGOING,
                message_type=MessageType.TEXT.value,
                channel="email",
                external_id=provider_response.get("id"),
                raw_content=str(provider_response),
            )

            return {
                "message_id": message.id,
                "session_id": session.id,
                "user_id": user.id,
                "external_id": message.external_id,
                "channel": message.channel,
            }

    def process_incoming_email(self, payload: Dict[str, Any]) -> None:
        """Process incoming email payload asynchronously."""
        try:
            with get_db() as db:
                user_repo = UserRepository(db)
                chat_repo = ChatRepository(db)
                message_repo = MessageRepository(db)

                inbound = self._parse_incoming_payload(payload)
                if inbound is None:
                    logger.warning("Email payload missing required fields: %s", payload)
                    return

                user = user_repo.get_by_email(inbound["from_email"])
                if not user:
                    user = user_repo.create_email_user(email=inbound["from_email"], name=inbound["from_name"])
                else:
                    user_repo.update_last_channel(user.id, "email")

                session = chat_repo.get_active_session_for_user(user.id, channel="email")
                if not session:
                    session_id = f"email_{user.id}_{int(datetime.utcnow().timestamp())}"
                    session = chat_repo.create_session(
                        user_id=user.id,
                        session_id=session_id,
                        channel="email",
                        ai_personality="ana",
                    )

                existing = None
                if inbound["external_id"]:
                    existing = message_repo.get_by_external_id(inbound["external_id"])
                if existing:
                    logger.info("Duplicate email message %s ignored", inbound["external_id"])
                    return

                incoming_message = message_repo.create_message(
                    user_id=user.id,
                    chat_session_id=session.id,
                    content=inbound["content"],
                    subject=inbound["subject"],
                    direction=MessageDirection.INCOMING,
                    message_type=MessageType.TEXT.value,
                    channel="email",
                    external_id=inbound["external_id"],
                    raw_content=str(payload),
                )

                reply_text = self._generate_ai_response(
                    db,
                    user_id=user.id,
                    session_id=session.id,
                    content=inbound["content"],
                )

                if reply_text:
                    self._send_ai_email_reply(inbound, reply_text, user, session, message_repo)

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Error processing incoming email: %s", exc)

    def _parse_incoming_payload(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract required fields from Resend webhook payload."""
        data = payload.get("data", {})
        email = data.get("email", {})

        from_header = email.get("from")
        subject = email.get("subject")
        text = email.get("text")
        message_id = email.get("id")

        if not (from_header and subject and message_id):
            return None

        name, address = self._split_from_header(from_header)

        return {
            "from_name": name,
            "from_email": address,
            "subject": subject,
            "content": text or email.get("html", ""),
            "external_id": message_id,
        }

    @staticmethod
    def _split_from_header(header: str) -> tuple[str, str]:
        if "<" in header and ">" in header:
            name_part, email_part = header.split("<", 1)
            return name_part.strip().strip('"'), email_part.strip().rstrip(">")
        return "", header

    def _generate_ai_response(
        self, db: Session, user_id: int, session_id: int, content: str
    ) -> Optional[str]:
        try:
            message_repo = MessageRepository(db)
            user_repo = UserRepository(db)
            chat_repo = ChatRepository(db)

            user = user_repo.get(user_id)
            session = chat_repo.get(session_id)
            if not user or not session:
                return None

            context = message_repo.get_conversation_context(session_id, max_messages=10)
            user_context = {
                "name": user.name,
                "email": user.email,
                "language": user.language,
                "total_messages": user.total_messages,
            }

            return self.ollama_service.generate_response(
                user_message=content,
                conversation_history=context,
                user_context=user_context,
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to generate AI response: %s", exc)
            return None

    def _send_ai_email_reply(
        self,
        inbound: Dict[str, Any],
        ai_text: str,
        user,
        session,
        message_repo: MessageRepository,
    ) -> None:
        try:
            metadata = {"in_reply_to": inbound["external_id"]}
            reply = awaitable(self.email_service.send_email)(
                to=inbound["from_email"],
                subject=f"Re: {inbound['subject']}",
                text=ai_text,
                metadata=metadata,
            )

            message_repo.create_message(
                user_id=user.id,
                chat_session_id=session.id,
                content=ai_text,
                subject=f"Re: {inbound['subject']}",
                direction=MessageDirection.OUTGOING,
                message_type=MessageType.TEXT.value,
                channel="email",
                external_id=reply.get("id"),
                raw_content=str(reply),
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to send AI email reply: %s", exc)


def awaitable(coro):
    """Helper to run coroutine in sync context."""
    import asyncio

    return asyncio.run(coro)
