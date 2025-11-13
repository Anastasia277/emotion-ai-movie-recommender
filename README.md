# Mood Predictor Web UI (Django)

This small Django app provides a webpage where you can upload a photo and receive a mood prediction, plus movie recommendations powered by two separate ML microservices.

What I added
- A new app `moodapp` with an upload page at the site root (`/`).
- An HTTP bridge in `moodapp/utils.py` that forwards uploads to an external mood model and then calls a movie recommendation service.
- Templates and CSS with a gray background, green actions, and follow-up questions (rating + vibe) for the user.
- Media support (uploaded images saved to `media/` and served in DEBUG).

How to run (Windows / PowerShell)

1. (Optional) Create and activate a virtual environment.

2. Install the dependencies:

```powershell
pip install -r requirements.txt
```

3. Provide the downstream service URLs (see below) via environment variables if they differ from the defaults.

4. Run Django checks and start the development server:

```powershell
python manage.py check
python manage.py runserver
```

5. Open http://127.0.0.1:8000/ and upload an image. The page will show the image, the predicted mood (with confidence when provided), and movie recommendations tailored to the selected rating + vibe options.

Configuring the microservices

- `MOOD_SERVICE_URL` (default: `http://127.0.0.1:8001/predict-mood`)
  - Django sends a `POST` request with the uploaded file (`image`) and expects a JSON response like:

```python
{"mood": "happy", "confidence": 0.87}
```

- `FASTAPI_URL` (default: `http://localhost:5001/recommend` – configured in `moodapp/utils.py`)
  - Django sends a `POST` request with a JSON payload such as `{"mood": "happy"}`. Rating / tone preferences are currently ignored by the new service.
  - Expected JSON example:

```
{
  "movies": [
    {"title": "The Grand Budapest Hotel", "rating": "PG-13", "reason": "Keeps the happy energy"},
    {"title": "Paddington 2", "rating": "PG", "reason": "Cozy and upbeat"}
  ]
}
```

`MOOD_SERVICE_URL` (for the mood detection service) and `SERVICE_TIMEOUT_SECONDS` can be overridden via environment variables.

Notes
- This is a development/demo setup. For production you must harden media/static serving, SECRET_KEY, DEBUG, and transport security for the microservice calls.
