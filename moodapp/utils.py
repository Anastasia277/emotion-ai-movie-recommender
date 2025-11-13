from __future__ import annotations

import logging
from typing import Dict

import requests
from django.conf import settings


logger = logging.getLogger(__name__)


FASTAPI_URL = "http://localhost:5001/recommend"


class ServiceError(Exception):
    """Raised when a downstream ML service cannot be reached or returns bad data."""


def _service_timeout() -> float:
    return getattr(settings, 'SERVICE_TIMEOUT_SECONDS', 10.0)


def predict_mood(image_path: str) -> Dict[str, object]:
    """Placeholder until the FastAPI mood detection service is integrated."""

    logger.warning('predict_mood called but no FastAPI mood service is configured', extra={'image_path': image_path})
    raise ServiceError('Mood prediction service has not been migrated to FastAPI yet.')


def get_recommendations(mood: str) -> Dict[str, object]:
    """Call the FastAPI recommendation service for a given mood."""

    try:
        response = requests.post(
            FASTAPI_URL,
            json={'mood': mood},
            timeout=_service_timeout(),
        )
    except requests.RequestException as exc:
        logger.exception('Error calling FastAPI recommendation service')
        raise ServiceError('Could not reach the recommendation service.') from exc

    try:
        response.raise_for_status()
        payload = response.json()
    except requests.HTTPError as exc:
        logger.exception('Recommendation service returned HTTP error: %s', exc)
        raise ServiceError('Recommendation service returned an error response.') from exc
    except ValueError as exc:
        logger.exception('Recommendation service returned invalid JSON: %s', exc)
        raise ServiceError('Recommendation service returned invalid data.') from exc

    if not isinstance(payload, dict):
        logger.error('Recommendation payload is not a dict: %s', payload)
        raise ServiceError('Recommendation service returned unexpected data.')

    return payload


def recommend_movies(*, mood: str, _rating_preference: str, _tone_preference: str) -> Dict[str, object]:
    """Backward-compatible wrapper that ignores rating/tone for the FastAPI backend."""

    payload = get_recommendations(mood)
    movies = payload.get('movies') or []

    if not movies:
        logger.warning('Recommendation service returned no movies: %s', payload)
        raise ServiceError('Recommendation service did not provide any movies.')

    return {
        'movies': movies,
        'details': payload,
    }
