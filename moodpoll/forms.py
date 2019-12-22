from django.forms import ModelForm
from .models import Poll


class PollForm(ModelForm):
    class Meta:
        model = Poll
        fields = ['title', 'description', 'optionlist']
        help_texts = {
            "title": 'Title of the poll',
            "description": 'Some additional information (optional).',
            "optionlist": 'List of options. Each line (ended by a line break) is a separate option',
        }
