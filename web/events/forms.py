from django.forms import CharField, ModelForm, Textarea
from django_better_admin_arrayfield.forms.fields import DynamicArrayField


class NotificationTemplateVariableForm(ModelForm):
    example_values = DynamicArrayField(base_field=CharField())


class NotificationTemplateForm(ModelForm):
    push_body = CharField(widget=Textarea)
    in_app_content = CharField(widget=Textarea)
