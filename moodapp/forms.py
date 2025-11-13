from django import forms


class UploadForm(forms.Form):
    image = forms.ImageField(label='Upload a photo')
    rating_preference = forms.CharField(widget=forms.HiddenInput(), initial='any', required=False)
    tone_preference = forms.CharField(widget=forms.HiddenInput(), initial='match', required=False)
