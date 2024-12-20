from django import forms
from .models import InspirationPDF

class InspirationPDFForm(forms.ModelForm):
    class Meta:
        model = InspirationPDF
        fields = ['title', 'pdf_file', 'preview_image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'pdf_file': forms.FileInput(attrs={'class': 'form-control'}),
            'preview_image': forms.FileInput(attrs={'class': 'form-control'})
        }

    def clean_pdf_file(self):
        pdf_file = self.cleaned_data.get('pdf_file')
        if pdf_file:
            if not pdf_file.name.endswith('.pdf'):
                raise forms.ValidationError('Only PDF files are allowed.')
            if pdf_file.size > 10 * 1024 * 1024:  # 10MB limit
                raise forms.ValidationError('File size cannot exceed 10MB.')
        return pdf_file

    def clean_preview_image(self):
        image = self.cleaned_data.get('preview_image')
        if image:
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise forms.ValidationError('Image size cannot exceed 5MB.')
            allowed_types = ['image/jpeg', 'image/png', 'image/gif']
            if image.content_type not in allowed_types:
                raise forms.ValidationError('Only JPEG, PNG and GIF images are allowed.')
        return image