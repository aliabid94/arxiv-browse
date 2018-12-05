"""Handle requests to support the home page."""

import os
import re
from flask import current_app
from typing import Any, Dict, Optional, Tuple
from werkzeug.exceptions import InternalServerError

from browse.services.database import get_document_count
from arxiv import status, taxonomy
from arxiv.base import logging
from arxiv.base.globals import get_application_config

app_config = get_application_config()
logger = logging.getLogger(__name__)

Response = Tuple[Dict[str, Any], int, Dict[str, Any]]

RE_TOTAL_PAPERS = re.compile(r'^total_papers\s+(?P<count>[0-9]+)',
                             re.MULTILINE)


def get_home_page() -> Response:
    """Get the data needed to generated the home page."""
    response_data: Dict[str, Any] = {}
    response_headers: Dict[str, Any] = {}

    try:
        response_data['groups'] = taxonomy.GROUPS
        response_data['archives'] = taxonomy.ARCHIVES_ACTIVE
        response_data['categories'] = taxonomy.CATEGORIES_ACTIVE
        response_data['document_count'] = _get_document_count()
        response_status = status.HTTP_200_OK
    except Exception as ex:
        logger.warning(f'Could not get abs page data: {ex}')
        raise InternalServerError

    return response_data, response_status, response_headers


def _get_document_count() -> Optional[int]:

    try:
        # check DB for document count first
        return get_document_count()  # type: ignore
    except Exception as ex:
        logger.warning(f'Error getting document count from DB: {ex}')

    try:
        # if DB is unavailable, fall back to legacy static file method
        daily_stats_path = current_app.config['BROWSE_DAILY_STATS_PATH']
        if daily_stats_path and os.path.isfile(daily_stats_path):
            with open(daily_stats_path, mode='r') as statsf:
                stats = statsf.read()
                stats_match = RE_TOTAL_PAPERS.match(stats)
                if stats_match:
                    return int(stats_match.group('count'))
        else:
            raise FileNotFoundError
    except (KeyError, FileNotFoundError):
        logger.warning(f'Daily stats file not found')

    return None