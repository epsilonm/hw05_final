from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Post, Comment, Group


class GroupForm(forms.ModelForm):
    """Form for creating groups."""
    class Meta:
        model = Group
        fields = ('title', 'description')

class PostForm(forms.ModelForm):
    """Form for creating and updating posts."""
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')
        labels = {
            'text': _('Текст поста'),
            'image': _('Картинка'),
        }
        help_texts = {
            'text': _('Текст нового поста'),
            'group': _('Группа, к которой будет относиться пост'),
        }


class CommentForm(forms.ModelForm):
    """Form for creating comments."""
    class Meta:
        model = Comment
        fields = ('text',)
        labels = {
            'text': _('Comment text'),
        }
