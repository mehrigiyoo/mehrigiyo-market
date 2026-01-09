from django import forms

from account.models import UserModel
from news.models import Notification


class NotificationAdminForm(forms.ModelForm):
    user = forms.ChoiceField(choices=(("0", 'All users'),))

    def __init__(self, *args, **kwargs):
        super(NotificationAdminForm, self).__init__(*args, **kwargs)
        self.fields['user'].choices += [(str(x.pk), f"{x.get_full_name()} | {x.username}") for x in UserModel.objects.all()]

    class Meta:
        model = Notification
        fields = ["title", "description", "image", "type", "user"]