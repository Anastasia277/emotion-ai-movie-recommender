from __future__ import annotations

import logging
import os
from typing import Dict

import numpy as np
import requests
import tensorflow_addons as tfa
from django.conf import settings
from PIL import Image
from tensorflow import keras


logger = logging.getLogger(__name__)


FASTAPI_URL = "http://localhost:5001/recommend"

# Load the Keras model once when the module is imported
MODEL_PATH = os.path.join(settings.BASE_DIR, 'Peach.keras')
try:
    # Load model with custom objects for tensorflow-addons optimizers
    emotion_model = keras.models.load_model(
        MODEL_PATH,
        custom_objects={'Addons>AdamW': tfa.optimizers.AdamW}
    )
    logger.info(f'Successfully loaded emotion model from {MODEL_PATH}')
except Exception as e:
    logger.error(f'Failed to load emotion model from {MODEL_PATH}: {e}')
    emotion_model = None

# Define emotion labels - adjust these based on your model's training
EMOTION_LABELS = ['angry', 'disgust', 'fear', 'happy', 'sad', 'surprise', 'neutral']


class ServiceError(Exception):
    """Raised when a downstream ML service cannot be reached or returns bad data."""


def _service_timeout() -> float:
    return getattr(settings, 'SERVICE_TIMEOUT_SECONDS', 10.0)


def preprocess_image(image_path: str, target_size=(224, 224)):
    """
    Preprocess the image for emotion prediction.
    The model expects 224x224 RGB images.
    """
    try:
        # Load image in RGB mode
        img = Image.open(image_path).convert('RGB')
        
        # Resize to target size
        img = img.resize(target_size)
        
        # Convert to numpy array and normalize to [0, 1]
        img_array = np.array(img, dtype=np.float32)
        img_array = img_array / 255.0
        
        # Add batch dimension
        img_array = np.expand_dims(img_array, axis=0)
        
        return img_array
    except Exception as e:
        logger.exception(f'Error preprocessing image {image_path}')
        raise ServiceError(f'Failed to preprocess image: {str(e)}')


def predict_mood(image_path: str) -> Dict[str, object]:
    """
    Predict emotion from an image using the loaded Keras model.
    Returns a dictionary with mood and confidence.
    """
    if emotion_model is None:
        logger.error('Emotion model is not loaded')
        raise ServiceError('Emotion prediction model is not available.')
    
    try:
        # Preprocess the image
        processed_image = preprocess_image(image_path)
        
        # Make prediction
        predictions = emotion_model.predict(processed_image, verbose=0)
        
        # Get the predicted emotion
        predicted_class = np.argmax(predictions[0])
        confidence = float(predictions[0][predicted_class])
        
        # Map to emotion label
        if predicted_class < len(EMOTION_LABELS):
            emotion = EMOTION_LABELS[predicted_class]
        else:
            emotion = 'unknown'
            logger.warning(f'Predicted class {predicted_class} is out of range for emotion labels')
        
        logger.info(f'Predicted emotion: {emotion} with confidence: {confidence:.2f}')
        
        return {
            'mood': emotion,
            'confidence': confidence,
            'all_predictions': {
                label: float(predictions[0][i]) 
                for i, label in enumerate(EMOTION_LABELS) 
                if i < len(predictions[0])
            }
        }
    except Exception as e:
        logger.exception(f'Error during emotion prediction for {image_path}')
        raise ServiceError(f'Failed to predict emotion: {str(e)}')


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


def recommend_movies(*, mood: str, rating_preference: str = 'any', tone_preference: str = 'match') -> Dict[str, object]:
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
