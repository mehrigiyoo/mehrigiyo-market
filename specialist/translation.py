from modeltranslation.translator import translator, TranslationOptions
from .models import TypeDoctor, Doctor


class TypeDoctorTranslation(TranslationOptions):
    fields = ('name',)


class DoctorTranslation(TranslationOptions):
    fields = ('full_name', 'description',)


translator.register(TypeDoctor, TypeDoctorTranslation)
translator.register(Doctor, DoctorTranslation)
