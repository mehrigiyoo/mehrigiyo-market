# import re
# import phonenumbers
# from django.utils.deconstruct import deconstructible
# from django.core.exceptions import ValidationError
#
#
# @deconstructible
# class PhoneValidator:
#     requires_context = False
#
#     @staticmethod
#     def clean(value):
#         return re.sub('[^0-9]+', '', value)
#
#     @staticmethod
#     def validate(value):
#         try:
#             z = phonenumbers.parse("+" + value)
#             if not phonenumbers.is_valid_number(z):
#                 return False
#         except:
#             return False
#
#         if len(value) != 12 or not value.startswith("998"):
#             return False
#
#         return True
#
#     def __call__(self, value):
#         if not PhoneValidator.validate(value):
#             raise ValidationError("Введенное значение не является номером телефона.")


import re
import phonenumbers
from django.utils.deconstruct import deconstructible
from django.core.exceptions import ValidationError

@deconstructible
class PhoneValidator:
    requires_context = False

    @staticmethod
    def clean(value):
        return re.sub('[^0-9]+', '', value)

    @staticmethod
    def validate(value):
        try:
            z = phonenumbers.parse("+" + value)
            if not phonenumbers.is_valid_number(z):
                return False
        except:
            return False

        return True

    def __call__(self, value):
        cleaned_value = PhoneValidator.clean(value)
        if not PhoneValidator.validate(cleaned_value):
            raise ValidationError("Введенное значение не является номером телефона.")

        if len(cleaned_value) != 12 or not cleaned_value.startswith("998"):
            raise ValidationError("Введенное значение не является номером телефона.")
