import datetime
from admin_auto_filters.filters import AutocompleteFilter

from django import forms
from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin

from news.forms import NotificationAdminForm
from shop.models import Feedbacks
from .models import NewsModel, Stories, TagsModel, Advertising, Notification, StoriesImage


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


class StoriesImageInline(admin.TabularInline):
    model = StoriesImage
    extra = 1  # default yangi bo'sh rasm qo'shish oynasi
    readonly_fields = ('id',)  # ID ni faqat o'qish uchun

@admin.register(Stories)
class StoriesAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'icon')
    search_fields = ('title',)
    inlines = [StoriesImageInline]


class AdvertisingAdmin(admin.ModelAdmin):
    list_display = ['id', 'image', 'title', 'text', 'medicine', 'doctor', 'type', ]
    list_filter = [MedicineFilter, DoctorFilter, 'type', ]
    search_fields = ['id', 'title', 'text', ]
    autocomplete_fields = ['medicine', 'doctor', ]


class FeedbackAdmin(admin.ModelAdmin):
    list_display = ['id', 'link', 'medicine', 'type', 'category', ]
    search_fields = ['id', 'link', 'medicine', ]
    list_filter = ['medicine', ]


admin.site.register(NewsModel, NewsModelAdmin)
admin.site.register(TagsModel, TagsModelAdmin)
admin.site.register(Advertising, AdvertisingAdmin)
admin.site.register(Feedbacks, FeedbackAdmin)
