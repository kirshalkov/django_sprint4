from django import forms
from .models import Post, Comment
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.contrib.auth import get_user_model


User = get_user_model()


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'location', 'category', 'image']
        widgets = {
            'pub_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'text': forms.Textarea(attrs={'rows': 5}),
        }
        labels = {
            'title': 'Заголовок',
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'location': 'Местоположение',
            'category': 'Категория',
            'image': 'Изображение',
        }
        help_texts = {
            'image': 'Загрузите изображение для поста (необязательно)',
        }
        



class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        labels = {
            'username': 'Логин',
            'first_name': 'Имя',
            'last_name': 'Фамилия',
            'email': 'Email',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'password' in self.fields:
            del self.fields['password']


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email')
        
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['first_name'].required = True
            self.fields['last_name'].required = True
            self.fields['username'].label = 'Логин'
            self.fields['first_name'].label = 'Имя'
            self.fields['last_name'].label = 'Фамилия'
            self.fields['email'].label = 'Email'
            self.fields['password1'].label = 'Пароль'
            self.fields['password2'].label = 'Подтверждение пароля'
            self.fields['email'].help_text = 'Необязательное поле'


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {'text': forms.Textarea(
            attrs={'rows': 3}
        )}
        labels = {
            'text': 'Комментарий',
        }
        