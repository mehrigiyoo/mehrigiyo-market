import datetime
from admin_auto_filters.filters import AutocompleteFilter

from django import forms
from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin

from news.forms import NotificationAdminForm
from news.tasks import send_notification_func
from shop.models import Feedbacks
from .models import NewsModel, Stories, StoriesContent, TagsModel, Advertising, Notification


class HashTagFilter(AutocompleteFilter):
    title = "Hash tag"
    field_name = 'hashtag'


class MedicineFilter(AutocompleteFilter):
    title = "Medicine"
    field_name = 'medicine'


class DoctorFilter(AutocompleteFilter):
    title = "Doctor"
    field_name = 'doctor'


class NewsModelAdmin(TabbedTranslationAdmin):
    date_hierarchy = 'created_at'
    list_display = ('id', 'image', 'name', 'hashtag', 'description', 'created_at',)
    list_filter = [HashTagFilter, ]
    search_fields = ['id', 'name', 'description', ]
    autocomplete_fields = ['hashtag', ]


class TagsModelAdmin(TabbedTranslationAdmin):
    list_display = ('id', 'tag_name',)
    search_fields = ['id', 'tag_name', ]


class StoriesAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'title_uz', 'title_ru', 'title_en', 'icon', ]
    search_fields = ['id', 'title', 'title_uz', 'title_ru', 'title_en', ],
    filter_horizontal = ['contents', ]


class StoriesContentAdmin(admin.ModelAdmin):
    list_display = ['id', 'content', 'content_uz', 'content_ru', 'content_en', 'type', ]
    list_filter = ['id', 'type', ]


class AdvertisingAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'title', 'text', 'medicine', 'doctor', 'type', ]
    list_filter = [MedicineFilter, DoctorFilter, 'type', ]
    search_fields = ['id', 'title', 'text', ]
    autocomplete_fields = ['medicine', 'doctor', ]

class NotificationAdmin(admin.ModelAdmin):
    form = NotificationAdminForm

    date_hierarchy = 'push_time'
    list_display = ['id', 'title', 'description', 'image', 'foreign_id', 'type', 'push_time', ]
    list_filter = ['type', ]
    search_fields = ['id', 'title', 'description', 'foreign_id', ]

    def save_model(self, request, obj, form, change):
        obj.foreign_id = form.cleaned_data['user']
        obj.save()

        send_notification_func.s(
            title = form.cleaned_data['title'],
            description = form.cleaned_data['description'],
            image_path = obj.image.path if obj.image else None,
            type = form.cleaned_data['type'],
            foreign_id = form.cleaned_data['user']
        # IDK!
        # ).apply_async(eta=obj.push_time + datetime.timedelta(seconds=30))
        ).apply_async(countdown=5)


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'link', 'medicine', 'type', 'category', ]
    search_fields = ['id', 'link', 'medicine', ]
    list_filter = ['medicine', ]


admin.site.register(NewsModel, NewsModelAdmin)
admin.site.register(TagsModel, TagsModelAdmin)
admin.site.register(Advertising, AdvertisingAdmin)
admin.site.register(Notification, NotificationAdmin)
admin.site.register(Stories, StoriesAdmin)
admin.site.register(StoriesContent, StoriesContentAdmin)
admin.site.register(Feedbacks, FeedbackAdmin)
