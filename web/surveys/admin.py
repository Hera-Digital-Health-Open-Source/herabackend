from django.contrib import admin

from surveys.models import Survey, SurveyTemplate, SurveyTemplateOption, SurveyTemplateTranslation, SurveySchedule


class SurveyTemplateOptionInline(admin.TabularInline):
    model = SurveyTemplateOption
    extra = 1


class SurveyTemplateTranslationInline(admin.TabularInline):
    model = SurveyTemplateTranslation
    max_num = 5


@admin.register(SurveyTemplate)
class SurveyTemplateAdmin(admin.ModelAdmin):
    list_display = ['code', 'survey_type', 'description']
    inlines = [SurveyTemplateTranslationInline, SurveyTemplateOptionInline]


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['survey_template', 'user']


@admin.register(SurveySchedule)
class SurveyScheduleAdmin(admin.ModelAdmin):
    ordering = ('calendar_event_type', 'offset_days', 'time_of_day',)
