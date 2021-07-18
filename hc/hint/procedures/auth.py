import logging

import hume_storage as storage

from hint.procedures import request_library
from hint.models import HintAuthentication


LOGGER = logging.getLogger(__name__)


def login_to_hint(hume_user):
    """
    Login to HINT.

    :param hume_user: HumeUser
    :returns: True on success, else False
    """
    session_id = request_library.login(hume_user)
    if session_id:
        LOGGER.info("logged in to HINT")
        hint_auth = HintAuthentication(session_id)
        storage.save(hint_auth)
        return True
    else:
        LOGGER.error("failed to authenticate with HINT")
        return False
