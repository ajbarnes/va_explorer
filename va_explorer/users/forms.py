from allauth.account.adapter import get_adapter
from allauth.account.forms import (
    PasswordField,
    PasswordVerificationMixin,
    SetPasswordField,
)
from django import forms
from django.contrib.auth import get_user_model, password_validation
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Group
from django.forms import ModelChoiceField, ModelMultipleChoiceField, RadioSelect
from django.utils.crypto import get_random_string
from va_explorer.va_data_management.models import Location

# from allauth.account.utils import send_email_confirmation, setup_user_email


User = get_user_model()


# Assigns user to national-level access implicitly if no locations are associated with the user.
def validate_location_access(form, geographic_access, locations):
    if geographic_access == "location-specific" and len(locations) == 0:
        form._errors["locations"] = form.error_class(
            ["You must add one or more locations if access is location-specific."]
        )
    elif geographic_access == "national" and len(locations) > 0:
        form._errors["locations"] = form.error_class(
            ["You cannot add specific locations if access is national."]
        )


# TODO: Update to Django 3.1 to get access to the instance via value without making another query
class LocationSelectMultiple(forms.SelectMultiple):
    def create_option(self, name, value, *args, **kwargs):
        option = super().create_option(name, value, *args, **kwargs)
        if value:
            instance = self.choices.queryset.get(pk=value)  # get instance
            option["attrs"]["data-depth"] = instance.depth  # set option attribute

            # Only query for descendants if there are any
            if instance.numchild > 0:
                option["attrs"]["data-descendants"] = instance.descendant_ids
        return option


class ExtendedUserCreationForm(UserCreationForm):
    """
    Extends the built in UserCreationForm in several ways:

    * The username is not visible.
    * Name field is added.
    * Group model from django.contrib.auth.models is represented as a ModelChoiceField
    * Non-model field geographic_access added to toggle between national and location-specific access
    * Data not saved by the default behavior of UserCreationForm is saved.
    """

    name = forms.CharField(required=True)
    password1 = None
    password2 = None
    # Allows us to save one group for the user, even though groups are m2m with user by default
    group = ModelChoiceField(queryset=Group.objects.all(), required=True)
    locations = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        widget=LocationSelectMultiple(attrs={"class": "location-select"}),
        required=False,
    )
    geographic_access = forms.ChoiceField(
        choices=(("national", "National"), ("location-specific", "Location-specific")),
        initial="location-specific",
        widget=RadioSelect(),
        required=True,
    )

    class Meta:
        model = User
        fields = ["name", "email", "group", "geographic_access", "locations"]

    def __init__(self, *args, **kwargs):
        """
        Set the request on the form class so that we can access the request when calling
        send_new_user_mail() in the save method below
        """
        self.request = kwargs.pop("request", None)

        super(UserCreationForm, self).__init__(*args, **kwargs)
        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(UserCreationForm, self).clean(*args, **kwargs)

        if "geographic_access" in cleaned_data and "locations" in cleaned_data:
            validate_location_access(
                self, cleaned_data["geographic_access"], cleaned_data["locations"]
            )

        return cleaned_data

    def save(self, commit=True):
        """
        Saves the email and name properties after the normal
        save behavior is complete. Sets a random password, which the user must
        change upon initial login.

        Saves the location and group after the user object is saved.
        """
        user = super(UserCreationForm, self).save(commit)

        if user:
            user.email = self.cleaned_data["email"]
            user.name = self.cleaned_data["name"]

            password = get_random_string(length=32)
            user.set_password(password)

            locations = self.cleaned_data["locations"]
            group = self.cleaned_data["group"]

            if commit:
                user.save()

                # You cannot associate the user with a m2m field until it’s been saved
                # https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
                user.locations.add(*locations)
                user.groups.add(*[group])

            # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
            # See allauth:
            # https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
            # setup_user_email(self.request, user, [])

            get_adapter().send_new_user_mail(self.request, user, password)

        return user


class UserUpdateForm(forms.ModelForm):
    """
    Similar to UserCreationForm but adds is_active field to allow an administrator
    to mark a user account as inactive
    """

    name = forms.CharField(required=True, max_length=100)
    group = ModelChoiceField(queryset=Group.objects.all(), required=True)
    locations = ModelMultipleChoiceField(
        queryset=Location.objects.all().order_by("path"),
        widget=LocationSelectMultiple(attrs={"class": "location-select"}),
        required=False,
    )
    geographic_access = forms.ChoiceField(
        choices=(("national", "National"), ("location-specific", "Location-specific")),
        widget=RadioSelect(),
        required=True,
    )

    class Meta:
        model = User
        fields = [
            "name",
            "email",
            "is_active",
            "group",
            "geographic_access",
            "locations",
        ]

    def __init__(self, *args, **kwargs):
        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # self.request = kwargs.pop("request", None)

        super(UserUpdateForm, self).__init__(*args, **kwargs)
        self.fields["group"].label = "Role"

    def clean(self, *args, **kwargs):
        """
        Normal cleanup
        """
        cleaned_data = super(forms.ModelForm, self).clean()

        if "geographic_access" in cleaned_data and "locations" in cleaned_data:
            validate_location_access(
                self, cleaned_data["geographic_access"], cleaned_data["locations"]
            )
        return cleaned_data

    def save(self, commit=True):
        user = super(UserUpdateForm, self).save(commit)
        locations = self.cleaned_data["locations"]
        group = self.cleaned_data["group"]

        if commit:
            """
            You cannot associate the user with a m2m field until it’s been saved
            https://docs.djangoproject.com/en/3.1/topics/db/examples/many_to_many/
            Set combines clear() and add(*locations)
            """
            user.locations.set(locations)
            user.groups.set([group])

        # TODO: Remove if we do not require email confirmation; we will no longer need the lines below
        # If the email address was changed, we add the new email address
        # if user.email != self.cleaned_data["email"]:
        #     user.add_email_address(self.request, self.cleaned_data["email"])

        """
        See allauth:
        https://github.com/pennersr/django-allauth/blob/c19a212c6ee786af1bb8bc1b07eb2aa8e2bf531b/allauth/account/utils.py
        send_email_confirmation(self.request, user, signup=False)
        """

        return user


class UserSetPasswordForm(PasswordVerificationMixin, forms.Form):
    """
    See allauth:
        https://github.com/pennersr/django-allauth/blob/master/allauth/account/forms.py#L54
        If we do not want this dependency, we can write our own clean method to ensure the
        2 typed-in passwords match.
    """

    password1 = SetPasswordField(
        label="New Password",
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = PasswordField(label="New Password (again)")

    def save(self, user):
        user.set_password(self.cleaned_data["password1"])
        user.has_valid_password = True
        user.save()

        return user
