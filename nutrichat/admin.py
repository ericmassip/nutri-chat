from django import forms
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.exceptions import ValidationError

from nutrichat.models import Attachment, User


class UserCreationForm(forms.ModelForm):
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = "__all__"

    def clean_password2(self):
        p1, p2 = self.cleaned_data.get("password1"), self.cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise ValidationError("Passwords don't match")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ["username", "password", "name", "surname", "role", "nutritionist", "description", "is_active", "is_admin"]


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 0
    readonly_fields = ["created", "last_updated"]


class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    list_display = ["username", "name", "surname", "role", "nutritionist", "is_active", "is_admin"]
    list_filter = ["role", "is_active"]
    fieldsets = [
        (None, {"fields": ["username", "password"]}),
        ("Personal info", {"fields": ["name", "surname"]}),
        ("Role", {"fields": ["role", "nutritionist", "description"]}),
        ("Permissions", {"fields": ["is_active", "is_admin"]}),
    ]
    add_fieldsets = [
        (None, {"classes": ["wide"], "fields": ["username", "role", "nutritionist", "password1", "password2"]}),
    ]
    search_fields = ["username", "name", "surname"]
    ordering = ["username"]
    filter_horizontal = []
    inlines = [AttachmentInline]


admin.site.register(User, UserAdmin)
