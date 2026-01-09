from modeltranslation.translator import translator, TranslationOptions
from .models import CountyModel, RegionModel


class CountryTranslation(TranslationOptions):
    fields = ('name',)


class RegionTranslation(TranslationOptions):
    fields = ('name',)


translator.register(CountyModel, CountryTranslation)
translator.register(RegionModel, RegionTranslation)
