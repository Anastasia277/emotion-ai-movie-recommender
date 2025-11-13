import os
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from .forms import UploadForm
from .utils import ServiceError, predict_mood, recommend_movies


DEFAULT_PREFERENCES = {
    'rating_preference': 'any',
    'tone_preference': 'match',
}


def index(request):
    context = {}
    if request.method == 'POST':
        form = UploadForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.cleaned_data['image']
            fs = FileSystemStorage(location=settings.MEDIA_ROOT)
            filename = fs.save(image.name, image)
            # try to obtain absolute path
            try:
                file_path = fs.path(filename)
            except Exception:
                file_path = os.path.join(settings.MEDIA_ROOT, filename)

            file_url = fs.url(filename)

            preferences = {
                'rating_preference': form.cleaned_data.get('rating_preference') or DEFAULT_PREFERENCES['rating_preference'],
                'tone_preference': form.cleaned_data.get('tone_preference') or DEFAULT_PREFERENCES['tone_preference'],
            }

            try:
                prediction = predict_mood(file_path)
                recommendations = recommend_movies(
                    mood=prediction['mood'],
                    rating_preference=preferences['rating_preference'],
                    tone_preference=preferences['tone_preference'],
                )
            except ServiceError as exc:
                context.update({
                    'form': UploadForm(initial=preferences),
                    'uploaded_file_url': file_url,
                    'preferences': preferences,
                    'preference_labels': None,
                    'recommendations': {},
                    'service_error': str(exc),
                })
                return render(request, 'moodapp/index.html', context)

            context.update({
                'form': UploadForm(initial=preferences),
                'uploaded_file_url': file_url,
                'prediction': prediction,
                'recommendations': recommendations,
                'preferences': preferences,
                'preference_labels': None,
            })
            return render(request, 'moodapp/index.html', context)
    else:
        form = UploadForm(initial=DEFAULT_PREFERENCES)

    context['form'] = form
    context['preferences'] = DEFAULT_PREFERENCES
    context['preference_labels'] = None
    context.setdefault('recommendations', {})
    return render(request, 'moodapp/index.html', context)
