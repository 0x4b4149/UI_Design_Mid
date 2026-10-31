from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

from .constants import SEVERITIES
from .models import Location, Profile


class StyledAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="帳號",
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "輸入會員帳號",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        label="密碼",
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "輸入密碼",
                "autocomplete": "current-password",
            }
        ),
    )


class RegisterForm(UserCreationForm):
    email = forms.EmailField(
        label="Email",
        required=True,
        widget=forms.EmailInput(
            attrs={"class": "field-input", "placeholder": "you@example.com"}
        ),
    )
    display_name = forms.CharField(
        label="顯示名稱",
        required=False,
        max_length=60,
        widget=forms.TextInput(
            attrs={"class": "field-input", "placeholder": "例如：Ivy Lin"}
        ),
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email", "display_name")
        labels = {"username": "會員帳號"}
        widgets = {
            "username": forms.TextInput(
                attrs={"class": "field-input", "placeholder": "設定登入帳號"}
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "密碼"
        self.fields["password2"].label = "確認密碼"
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update(
                {"class": "field-input", "placeholder": "至少 8 個字元"}
            )
        self.order_fields(["username", "email", "display_name", "password1", "password2"])

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("這個 Email 已經註冊過了。")
        return email

    def save(self, commit=True):
        user = super().save(commit=commit)
        if commit:
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.display_name = self.cleaned_data.get("display_name", "")
            profile.save()
        return user


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = (
            "display_name",
            "unit",
            "home_location",
            "notify_app",
            "notify_email",
            "notify_sms",
            "min_severity",
        )
        labels = {
            "display_name": "顯示名稱",
            "unit": "偏好溫度單位",
            "home_location": "預設城市",
            "notify_app": "App 推播",
            "notify_email": "Email 通知",
            "notify_sms": "簡訊通知",
            "min_severity": "通知門檻",
        }
        widgets = {
            "display_name": forms.TextInput(attrs={"class": "field-input"}),
            "unit": forms.Select(attrs={"class": "field-input"}),
            "home_location": forms.Select(attrs={"class": "field-input"}),
            "min_severity": forms.Select(attrs={"class": "field-input"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["home_location"].queryset = Location.objects.order_by("state", "name")
        self.fields["home_location"].empty_label = "不指定（首頁顯示 New York）"
        self.fields["min_severity"].choices = [
            ("minor", "全部警報（含 Minor）"),
            ("moderate", "Moderate 以上（推薦）"),
            ("severe", "僅 Severe"),
        ]
        for name in ("notify_app", "notify_email", "notify_sms"):
            self.fields[name].widget.attrs["class"] = "switch-input"
