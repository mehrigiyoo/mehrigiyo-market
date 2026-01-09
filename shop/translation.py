from modeltranslation.translator import translator, TranslationOptions
from .models import TypeMedicine, Medicine


class TypeMedicineTranslation(TranslationOptions):
    fields = ('name',)


class MedicineTranslation(TranslationOptions):
    fields = ('name', 'title', 'description')


translator.register(TypeMedicine, TypeMedicineTranslation)
translator.register(Medicine, MedicineTranslation)
