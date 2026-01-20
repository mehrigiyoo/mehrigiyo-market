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
from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible


def normalize_phone(value: str) -> str:
    """
    +998 90 123 45 67
    998901234567
    0901234567
    => 998901234567
    """
    value = re.sub(r'[^0-9]+', '', value)

    if value.startswith("998") and len(value) == 12:
        return value

    if value.startswith("0") and len(value) == 10:
        return "998" + value[1:]

    raise ValidationError("Telefon raqam noto‘g‘ri")


@deconstructible
class PhoneValidator:
    def __call__(self, value):
        try:
            phone = normalize_phone(value)
            parsed = phonenumbers.parse("+" + phone)
            if not phonenumbers.is_valid_number(parsed):
                raise ValidationError
        except Exception:
            raise ValidationError("Telefon raqam noto‘g‘ri")
