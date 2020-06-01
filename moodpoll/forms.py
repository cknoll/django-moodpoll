from django.forms import ModelForm
from .models import Poll


class PollForm(ModelForm):
    class Meta:
        model = Poll
        fields = ['title', 'description', 'replies_hidden']
        help_texts = {
            "title": 'Title of the poll',
            "description": 'Some additional information about the poll (optional, markdown enabled).',
            "replies_hidden": 'Enable to hide the replies. Otherwise all replies will be public.',
        }

