from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import transaction
from markdownx.widgets import MarkdownxWidget

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Column, Layout, Row

from nutrichat.models import Attachment, User


def validate_pdf_content_type(file):
    file.seek(0)
    header = file.read(4)
    file.seek(0)
    if header != b'%PDF':
        raise ValidationError('Only PDF files are allowed.')


class CustomerEditForm(forms.ModelForm):
    file = forms.FileField(
        required=False,
        validators=[FileExtensionValidator(['pdf']), validate_pdf_content_type],
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf'}),
    )

    class Meta:
        model = User
        fields = ['name', 'surname', 'description']
        widgets = {
            'description': MarkdownxWidget(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('surname', css_class='col-md-6'),
            ),
            'description',
        )

    def save(self, commit=True):
        with transaction.atomic():
            user = super().save(commit=commit)
            if commit and self.cleaned_data.get('file'):
                user.attachments.all().delete()
                Attachment.objects.create(user=user, file=self.cleaned_data['file'])
        return user


class CustomerCreateForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )
    password_confirm = forms.CharField(
        label="Confirm password",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta:
        model = User
        fields = ['username']

    def __init__(self, *args, nutritionist=None, **kwargs):
        self._nutritionist = nutritionist
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            'username',
            Row(
                Column('password', css_class='col-md-6'),
                Column('password_confirm', css_class='col-md-6'),
            ),
        )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('password') != cleaned_data.get('password_confirm'):
            self.add_error('password_confirm', "Passwords do not match.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.CUSTOMER
        user.nutritionist = self._nutritionist
        user.username = user.username.lower()
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user
