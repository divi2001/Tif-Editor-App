from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import InspirationPDF, PDFLike
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import InspirationPDF, PDFLike
from .forms import InspirationPDFForm
from django.urls import reverse

# Admin Dashboard View

def admin_dashboard(request):
    pdfs = InspirationPDF.objects.all().order_by('-created_at')
    context = {
        'pdfs': pdfs,
        'total_pdfs': pdfs.count(),
        'total_likes': sum(pdf.likes_count for pdf in pdfs)
    }
    return render(request, 'dashboard.html', context)

# PDF Upload View

def upload_pdf(request):
    if request.method == 'POST':
        form = InspirationPDFForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                pdf = form.save()
                messages.success(request, f'PDF "{pdf.title}" was successfully uploaded!')
                return redirect('mainadmin:dashboard')
            except Exception as e:
                messages.error(request, f'Error uploading PDF: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = InspirationPDFForm()
    
    return render(request, 'upload_pdf.html', {'form': form})

# PDF Edit View

def edit_pdf(request, pdf_id):
    pdf = get_object_or_404(InspirationPDF, id=pdf_id)
    
    if request.method == 'POST':
        form = InspirationPDFForm(request.POST, request.FILES, instance=pdf)
        if form.is_valid():
            try:
                pdf = form.save()
                messages.success(request, f'PDF "{pdf.title}" was successfully updated!')
                return redirect('mainadmin:dashboard')
            except Exception as e:
                messages.error(request, f'Error updating PDF: {str(e)}')
    else:
        form = InspirationPDFForm(instance=pdf)
    
    return render(request, 'edit_pdf.html', {
        'form': form,
        'pdf': pdf
    })

# PDF Delete View

def delete_pdf(request, pdf_id):
    pdf = get_object_or_404(InspirationPDF, id=pdf_id)
    
    if request.method == 'POST':
        try:
            title = pdf.title
            pdf.delete()
            messages.success(request, f'PDF "{title}" was successfully deleted!')
        except Exception as e:
            messages.error(request, f'Error deleting PDF: {str(e)}')
        return redirect('mainadmin:dashboard')
    
    return render(request, 'delete_confirm.html', {'pdf': pdf})

# PDF Download View
def download_pdf(request, pdf_id):
    pdf = get_object_or_404(InspirationPDF, id=pdf_id)
    try:
        response = FileResponse(pdf.pdf_file, as_attachment=True)
        response['Content-Disposition'] = f'attachment; filename="{pdf.title}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f'Error downloading PDF: {str(e)}')
        return redirect('mainadmin:dashboard')

# Like Toggle View
@require_POST

def toggle_like(request, pdf_id):
    try:
        pdf = get_object_or_404(InspirationPDF, id=pdf_id)
        like, created = PDFLike.objects.get_or_create(
            user=request.user,
            pdf=pdf
        )
        
        if not created:
            like.delete()
            liked = False
        else:
            liked = True

        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': pdf.likes_count
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        }, status=400)

# PDF List View for Main Site
def pdf_list(request):
    pdfs = InspirationPDF.objects.all().order_by('-created_at')
    context = {
        'pdfs': pdfs,
        'user': request.user
    }
    return render(request, 'pdf_list.html', context)

def toggle_like(request, pdf_id):
    try:
        pdf = InspirationPDF.objects.get(id=pdf_id)
        like, created = PDFLike.objects.get_or_create(
            user=request.user,
            pdf=pdf
        )
        
        if not created:
            # User already liked the PDF, so unlike it
            like.delete()
            liked = False
        else:
            liked = True

        return JsonResponse({
            'status': 'success',
            'liked': liked,
            'likes_count': pdf.likes_count
        })
    except InspirationPDF.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'PDF not found'
        }, status=404)