import logging

from sqlalchemy import event
from sqlalchemy.orm import Session

from app.media.storage import MediaStorageError

logger = logging.getLogger(__name__)


def _after_commit(session: Session) -> None:
    session.info.pop("media_pending_uploads", None)
    pending_deletes = session.info.pop("media_pending_deletes", [])
    for storage, key in pending_deletes:
        try:
            storage.delete(key)
        except MediaStorageError:
            logger.exception("Unable to remove an orphaned media object after database commit.")


def _after_rollback(session: Session) -> None:
    pending_uploads = session.info.pop("media_pending_uploads", [])
    session.info.pop("media_pending_deletes", None)
    for storage, key in pending_uploads:
        try:
            storage.delete(key)
        except MediaStorageError:
            logger.exception("Unable to clean up a media object after database rollback.")


event.listen(Session, "after_commit", _after_commit)
event.listen(Session, "after_rollback", _after_rollback)
