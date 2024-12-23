from django.contrib import admin
from django import forms
from .models import (
    SubscriptionPlan, UserSubscription, InspirationPDF, PDFLike,
    Palette, Color
)
from django.utils.html import format_html

from django.http import JsonResponse
from django.urls import path


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



class ColorAdminForm(forms.ModelForm):
    color_picker = forms.CharField(widget=forms.TextInput(attrs={'type': 'color', 'class': 'color-picker'}), required=False)

    class Meta:
        model = Color
        fields = ['red', 'green', 'blue', 'color_picker']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['color_picker'].initial = f'#{self.instance.red:02x}{self.instance.green:02x}{self.instance.blue:02x}'
        
        # Add classes to RGB inputs for easier selection
        self.fields['red'].widget.attrs['class'] = 'rgb-input'
        self.fields['green'].widget.attrs['class'] = 'rgb-input'
        self.fields['blue'].widget.attrs['class'] = 'rgb-input'

class ColorInline(admin.TabularInline):
    model = Color
    form = ColorAdminForm
    extra = 0  # Set to 0 as we'll dynamically set this based on num_colors

class PaletteAdminForm(forms.ModelForm):
    class Meta:
        model = Palette
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['num_colors'].widget.attrs['readonly'] = True
@admin.register(Palette)
class PaletteAdmin(admin.ModelAdmin):
    form = PaletteAdminForm
    list_display = ('name', 'creator', 'favorites_count', 'num_colors', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('name', 'creator__username')
    inlines = [ColorInline]

    def get_inline_instances(self, request, obj=None):
        inline_instances = super().get_inline_instances(request, obj)
        for inline in inline_instances:
            if isinstance(inline, ColorInline):
                if obj:
                    inline.extra = obj.num_colors - obj.colors.count()
                else:
                    inline.extra = 5  # Default to 5 colors for new palettes
        return inline_instances

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        
        current_color_count = obj.colors.count()
        new_color_count = obj.num_colors

        if current_color_count < new_color_count:
            # Add new colors
            for _ in range(new_color_count - current_color_count):
                Color.objects.create(palette=obj, red=255, green=255, blue=255)  # Default to white
        elif current_color_count > new_color_count:
            # Remove excess colors
            obj.colors.order_by('-id')[:current_color_count - new_color_count].delete()

    def save_formset(self, request, form, formset, change):
        instances = formset.save(commit=False)
        for instance in instances:
            instance.save()
        formset.save_m2m()
        
        # Update num_colors to match the actual number of colors
        form.instance.num_colors = form.instance.colors.count()
        form.instance.save()

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('<int:palette_id>/update_colors/', self.update_colors_view, name='update_palette_colors'),
        ]
        return custom_urls + urls

    def update_colors_view(self, request, palette_id):
        palette = Palette.objects.get(id=palette_id)
        new_num_colors = int(request.POST.get('num_colors', palette.num_colors))
        current_color_count = palette.colors.count()

        if current_color_count < new_num_colors:
            # Add new colors
            for _ in range(new_num_colors - current_color_count):
                Color.objects.create(palette=palette, red=255, green=255, blue=255)  # Default to white
        elif current_color_count > new_num_colors:
            # Remove excess colors
            palette.colors.order_by('-id')[:current_color_count - new_num_colors].delete()

        palette.num_colors = new_num_colors
        palette.save()

        return JsonResponse({'status': 'success', 'new_num_colors': new_num_colors})

    class Media:
        js = ('admin/js/jquery.min.js', 'admin/js/color_pickr.js', 'admin/js/palette_admin.js')

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
        js = (
            'https://code.jquery.com/jquery-3.6.0.min.js',  # Add jQuery
            'admin/js/color_pickr.js',
        )
        css = {
            'all': ('admin/css/color_picker.css',)
        }