from django.conf import settings
from django.db import models
from django.core.validators import FileExtensionValidator,MinValueValidator,MaxValueValidator
from django.utils import timezone

class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    duration_in_days = models.IntegerField()

    def __str__(self):
        return self.name

class UserSubscription(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField()
    active = models.BooleanField(default=True)

    def is_active(self):
        return self.end_date > timezone.now() and self.active

    def __str__(self):
        return f'{self.user.username} - {self.plan.name}'

class InspirationPDF(models.Model):
    title = models.CharField(max_length=200)
    pdf_file = models.FileField(
        upload_to='pdfs/',
        validators=[FileExtensionValidator(['pdf'])]
    )
    preview_image = models.ImageField(
        upload_to='pdf_previews/',
        help_text="Preview image for the PDF"
    )
    likes_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def update_likes_count(self):
        self.likes_count = self.pdf_likes.count()
        self.save()

class PDFLike(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    pdf = models.ForeignKey(
        InspirationPDF, 
        on_delete=models.CASCADE,
        related_name='pdf_likes'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'pdf')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.pdf.update_likes_count()

    def delete(self, *args, **kwargs):
        pdf = self.pdf
        super().delete(*args, **kwargs)
        pdf.update_likes_count()


class Palette(models.Model):
    name = models.CharField(max_length=100)
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='created_palettes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorites_count = models.IntegerField(default=0)
    num_colors = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)])

    def __str__(self):
        return self.name

    def update_favorites_count(self):
        self.favorites_count = self.palette_favorites.count()
        self.save()

class Color(models.Model):
    palette = models.ForeignKey(Palette, on_delete=models.CASCADE, related_name='colors')
    red = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    green = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])
    blue = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(255)])

    def __str__(self):
        return f"RGB({self.red}, {self.green}, {self.blue})"

class PaletteFavorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_palettes')
    palette = models.ForeignKey(Palette, on_delete=models.CASCADE, related_name='palette_favorites')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'palette')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.palette.update_favorites_count()

    def delete(self, *args, **kwargs):
        palette = self.palette
        super().delete(*args, **kwargs)
        palette.update_favorites_count()