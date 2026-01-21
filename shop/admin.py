from admin_auto_filters.filters import AutocompleteFilter

from django.contrib import admin
from modeltranslation.admin import TabbedTranslationAdmin
from .models import Medicine, TypeMedicine, OrderModel, CartModel, PicturesMedicine, DeliveryMan


class TypeMedicineFilter(AutocompleteFilter):
    title = "Type medicine"
    field_name = 'type_medicine'


class UserFilter(AutocompleteFilter):
    title = "User"
    field_name = 'user'


class ProductFilter(AutocompleteFilter):
    title = "Product"
    field_name = 'product'


class CreditCardFilter(AutocompleteFilter):
    title = "Credit card"
    field_name = 'credit_card'


class ShippingAddressFilter(AutocompleteFilter):
    title = "Shipping address"
    field_name = 'shipping_address'


class DeliveryFilter(AutocompleteFilter):
    title = "Delivery"
    field_name = 'delivery'


class PicturesMedicineInline(admin.TabularInline):
    model = PicturesMedicine
    extra = 1
    max_num = 10


class TypeMedicineAdmin(TabbedTranslationAdmin):
    list_display = ('id', 'name', 'image', 'icon')
    search_fields = ['id', 'name', ]


class MedicineAdmin(TabbedTranslationAdmin):
    date_hierarchy = 'created_at'
    list_display = (
        'id', 'name', 'title', 'image', 'order_count', 'description', 'quantity', 'review', 'weight', 'type_medicine',
        'cost', 'discount', 'created_at',)
    list_filter = [TypeMedicineFilter, ]
    search_fields = ['id', 'name', 'title', 'order_count', 'description', 'quantity', 'review', 'weight', 'cost',
                     'discount', ]
    autocomplete_fields = ['type_medicine', ]
    inlines = [PicturesMedicineInline]



class CartModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'amount', 'status', ]
    list_filter = [UserFilter, ProductFilter, 'status', ]
    search_fields = ['id', 'amount', ]
    autocomplete_fields = ['user', 'product', ]


class DeliveryManAdmin(admin.ModelAdmin):
    list_display = ['id', 'full_name', 'phone', ]
    search_fields = ['id', 'full_name', 'phone', ]


admin.site.register(DeliveryMan, DeliveryManAdmin)


class OrderModelAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = ['id', 'user', 'credit_card', 'shipping_address', 'price', 'payment_type', 'payment_status',
                    'delivery_status', 'delivery', 'created_at', ]
    list_filter = [UserFilter, CreditCardFilter, ShippingAddressFilter, 'payment_type', 'payment_status',
                   'delivery_status', DeliveryFilter, ]
    search_fields = ['id', 'price', ]
    autocomplete_fields = ['user', 'credit_card', 'shipping_address', 'delivery', ]
    filter_horizontal = ['cart_products', ]


admin.site.register(Medicine, MedicineAdmin)
admin.site.register(TypeMedicine, TypeMedicineAdmin)
admin.site.register(OrderModel, OrderModelAdmin)
admin.site.register(CartModel, CartModelAdmin)
