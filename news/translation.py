from modeltranslation.translator import translator, TranslationOptions
from .models import NewsModel, TagsModel, Advertising


class NewsTranslation(TranslationOptions):
    fields = ('name', 'description',)


class AdvertisingTranslation(TranslationOptions):
    fields = ('title', 'text', 'image',)


class TagsTranslation(TranslationOptions):
    fields = ('tag_name', )


translator.register(NewsModel, NewsTranslation)
translator.register(Advertising, AdvertisingTranslation)
translator.register(TagsModel, TagsTranslation)
