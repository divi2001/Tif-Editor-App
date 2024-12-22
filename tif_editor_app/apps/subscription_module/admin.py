from django.contrib import admin
from django import forms
from .models import (
    SubscriptionPlan, UserSubscription, InspirationPDF, PDFLike,
    Palette, Color
)
from django.utils.html import format_html

# Register SubscriptionPlan and UserSubscription using admin.site.register()
admin.site.register(SubscriptionPlan)
admin.site.register(UserSubscription)

# Custom admin classes for SubscriptionPlan and UserSubscription
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_in_days')

class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'start_date', 'end_date', 'active')
    list_filter = ('active', 'plan')
    search_fields = ('user__username', 'user__email')

# Re-register SubscriptionPlan and UserSubscription with custom admin classes
admin.site.unregister(SubscriptionPlan)
admin.site.unregister(UserSubscription)
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(UserSubscription, UserSubscriptionAdmin)

# Register InspirationPDF and PDFLike using the @admin.register decorator
@admin.register(InspirationPDF)
class InspirationPDFAdmin(admin.ModelAdmin):
    list_display = ('title', 'likes_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title',)

@admin.register(PDFLike)
class PDFLikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'pdf', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'pdf__title')


class ColorInline(admin.TabularInline):
    model = Color
    extra = 1


class ColorAdminForm(forms.ModelForm):
    color_picker = forms.CharField(widget=forms.TextInput(attrs={'type': 'color'}), required=False)

    class Meta:
        model = Color
        fields = ['red', 'green', 'blue', 'color_picker']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['color_picker'].initial = f'#{self.instance.red:02x}{self.instance.green:02x}{self.instance.blue:02x}'

class ColorInline(admin.TabularInline):
    model = Color
    form = ColorAdminForm
    extra = 1

@admin.register(Palette)
class PaletteAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'favorites_count', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'creator__username')
    inlines = [ColorInline]

    class Media:
        js = ('admin/js/color_picker.js',)

@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    form = ColorAdminForm
    list_display = ('palette', 'display_color', 'red', 'green', 'blue')
    list_filter = ('palette',)

    def display_color(self, obj):
        return format_html(
            '<div style="background-color: rgb({}, {}, {}); width: 30px; height: 30px;"></div>',
            obj.red, obj.green, obj.blue
        )
    display_color.short_description = 'Color'

    class Media:
        js = ('admin/js/color_picker.js',)