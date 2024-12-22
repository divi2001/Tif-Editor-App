import os
import psdtags
import numpy as np
from PIL import Image
from collections import Counter
from psdtags import PsdChannelId
from .forms import TiffUploadForm
from django.shortcuts import render
from psdtags.psdtags import TiffImageSourceData, PsdChannelId
from tifffile import TiffFile, imshow,imwrite,imsave
from matplotlib import pyplot
from django.http import HttpResponse
from django.http import JsonResponse
from django.conf import settings
import os
from PIL import Image
import json
from django.views.decorators.csrf import csrf_exempt
from PIL import Image
import io
from PIL import Image
from django.views import View
import colorsys
from typing import Dict, List, Optional

from colorsys import rgb_to_hls
import base64

import imagecodecs
from PIL import ImageOps
import cv2
import logging
from .getcolors import analyze_image_colors
from io import BytesIO

logger = logging.getLogger(__name__)
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.shortcuts import render
from apps.subscription_module.models import InspirationPDF,PDFLike

class InspirationView(View):
    def get(self, request):
        pdfs = InspirationPDF.objects.all().order_by('-created_at')
        pdfs_data = []

        for pdf in pdfs:
            liked = PDFLike.objects.filter(user=request.user, pdf=pdf).exists() if request.user.is_authenticated else False
            pdfs_data.append({
                'id': pdf.id,
                'title': pdf.title,
                'preview_image': pdf.preview_image.url if pdf.preview_image else None,
                'pdf_url': pdf.pdf_file.url if pdf.pdf_file else None,
                'likes_count': pdf.likes_count,
                'created_at': pdf.created_at.strftime('%Y-%m-%d'),
                'liked': liked
            })
        
        return JsonResponse({'pdfs': pdfs_data})

    @method_decorator(login_required)
    def post(self, request):
        pdf_id = request.POST.get('pdf_id')
        pdf = InspirationPDF.objects.get(id=pdf_id)
        like, created = PDFLike.objects.get_or_create(user=request.user, pdf=pdf)
        
        if not created:
            # User has already liked this PDF, so unlike it
            like.delete()
            liked = False
        else:
            liked = True
        
        return JsonResponse({
            'liked': liked,
            'likes_count': pdf.likes_count
        })

inspiration_view = InspirationView.as_view()


@csrf_exempt
def analyze_color(request):
    if request.method == 'POST':
        try:
            # Parse JSON data
            data = json.loads(request.body)
            
            if 'imageData' not in data:
                return JsonResponse({
                    'success': False,
                    'error': 'No imageData field in request'
                })

            image_data = data['imageData']
            
            if not image_data:
                return JsonResponse({
                    'success': False,
                    'error': 'Empty image data'
                })

            # Process base64 data
            try:
                # Remove data URL prefix if present
                if isinstance(image_data, str) and 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]
                
                image_bytes = base64.b64decode(image_data)
                image = Image.open(io.BytesIO(image_bytes))
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f'Error processing image data: {str(e)}'
                })

            result = analyze_image_colors(image)
            
            if result:
                return JsonResponse({
                    'success': True,
                    'colors': result
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'Color analysis failed'
                })

        except json.JSONDecodeError as e:
            return JsonResponse({
                'success': False,
                'error': f'Invalid JSON: {str(e)}'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}'
            })

    return JsonResponse({
        'success': False,
        'error': 'Method not allowed'
    })


def process_svg_upload(request):
    if request.method == 'POST':
        try:
            tiff_file = request.FILES['tiff_file']
            file_path = os.path.join(settings.MEDIA_ROOT, tiff_file.name)
            output_dir = os.path.join(settings.MEDIA_ROOT, 'output', os.path.splitext(tiff_file.name)[0])

            # Create directories if they don't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            os.makedirs(output_dir, exist_ok=True)

            # Save uploaded file
            with open(file_path, 'wb+') as destination:
                for chunk in tiff_file.chunks():
                    destination.write(chunk)

            # Process the TIFF file
            layers = extract_layers(file_path, output_dir)
            
            # Update paths to use MEDIA_URL
            for layer in layers:
                relative_path = layer['path'].replace('\\', '/').split('media/')[-1]
                layer['path'] = settings.MEDIA_URL + relative_path

            # Get image dimensions
            with Image.open(file_path) as img:
                width, height = img.size

            # Store the layers information in session
            request.session['current_layers'] = layers
            request.session['image_width'] = width
            request.session['image_height'] = height

            return JsonResponse({
                'success': True,
                'layer_count': len(layers),
                'layers': layers,
                'width': width,
                'height': height
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })
    
    # For GET requests, get layers from session if available
    layers = request.session.get('current_layers', [])
    width = request.session.get('image_width', 0)
    height = request.session.get('image_height', 0)
    
    return render(request, 'layers.html', {
        'layer_count': len(layers),
        'layers': layers,
        'width': width,
        'height': height
    })

def upload_tiff(request):
    if request.method == 'POST':
        form = TiffUploadForm(request.POST, request.FILES)
        if form.is_valid():
            tiff_file = request.FILES['tiff_file']
            file_path = os.path.join('media', tiff_file.name)

            with open(file_path, 'wb+') as destination:
                for chunk in tiff_file.chunks():
                    destination.write(chunk)
            # Process the TIFF file

            layers = extract_layers(file_path, 'media/output/'+tiff_file.name)
            # Convert backslashes to forward slashes in layer paths
            for layer in layers:
                layer['path'] = layer['path'].replace('\\', '/')
            print(layers)

            with Image.open(file_path) as img:
                width, height = img.size
            # return render(request, 'single_layers.html', {'layers': layers})
            return render(request, 'layers.html', {'layer_count':len(layers),'layers': layers,'width':width,
                            'height':height})
    else:
        form = TiffUploadForm()
    return render(request, 'upload.html', {'form': form})

@csrf_exempt
def export_tiff(request):
    if request.method == 'POST':
        try:
            total_layers = int(request.POST.get('total_layers'))

            # Find the minimum and maximum coordinates of the layers
            min_left = float('inf')
            min_top = float('inf')
            max_right = float('-inf')
            max_bottom = float('-inf')
            for layer in range(1, total_layers + 1):
                layer_position_from_top = int(request.POST.get(f'position_from_top_{layer}', 0))
                layer_position_from_left = int(request.POST.get(f'position_from_left_{layer}', 0))
                layer_width = int(request.POST.get(f'width_{layer}'))
                layer_height = int(request.POST.get(f'height_{layer}'))
                min_left = min(min_left, layer_position_from_left)
                min_top = min(min_top, layer_position_from_top)
                max_right = max(max_right, layer_position_from_left + layer_width)
                max_bottom = max(max_bottom, layer_position_from_top + layer_height)

            # Calculate the dimensions of the TIFF image
            tiff_width = max_right - min_left
            tiff_height = max_bottom - min_top

            # Create a blank TIFF image with the calculated dimensions
            tiff_image = Image.new('RGBA', (tiff_width, tiff_height), (0, 0, 0, 0))

            for layer in range(1, total_layers + 1):
                layer_position_from_top = int(request.POST.get(f'position_from_top_{layer}', 0))
                layer_position_from_left = int(request.POST.get(f'position_from_left_{layer}', 0))
                layer_width = int(request.POST.get(f'width_{layer}'))
                layer_height = int(request.POST.get(f'height_{layer}'))
                layer_data = request.FILES[f'data_{layer}'].read()

                # Skip layers with zero height or width
                if layer_height == 0 or layer_width == 0:
                    continue

                # Create a PIL Image from the layer data
                layer_image = Image.frombytes('RGBA', (layer_width, layer_height), layer_data)

                # Calculate the position of the layer relative to the TIFF image
                layer_left = layer_position_from_left - min_left
                layer_top = layer_position_from_top - min_top

                # Paste the layer image onto the TIFF image at the calculated position
                tiff_image.paste(layer_image, (layer_left, layer_top))

            # Create a BytesIO object to store the TIFF data
            tiff_data = io.BytesIO()

            # Save the TIFF image to the BytesIO object
            tiff_image.save(tiff_data, format='TIFF')

            # Set the BytesIO object's position to the beginning
            tiff_data.seek(0)

            # Create a response with the TIFF data
            response = HttpResponse(tiff_data.getvalue(), content_type='image/tiff')
            response['Content-Disposition'] = 'attachment; filename="output.tif"'

            return response
        except Exception as e:
            print(f"Error in export_tiff view: {str(e)}")
            return HttpResponse(f'Error: {str(e)}', status=500)

    # Return an error response if the request method is not POST
    return HttpResponse('Invalid request method', status=405)

def get_layer_image(layer):
    try:
        channels_data = []
        for channel in layer.channels:
            if channel.channelid in [PsdChannelId.CHANNEL0, PsdChannelId.CHANNEL1, PsdChannelId.CHANNEL2]:
                if channel.data.ndim == 2:
                    channels_data.append(channel.data)
                else:
                    print(
                        f"Unexpected channel data shape: {channel.data.shape}")

        if len(channels_data) == 3:
            image_data = np.stack(channels_data, axis=-1)
            return image_data
        else:
            print(f"Unexpected number of channels: {len(channels_data)}")
            return None
    except Exception as e:
        print(f"Error retrieving layer image: {str(e)}")
        return None

def extract_layers(file_path, output_dir):
    isd = TiffImageSourceData.fromtiff(file_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    layers_info = []
    if isd.layers:

        for layer in isd.layers:

            image = layer.asarray()
            # image_pros = get_layer_image(layer)
            # unique_colors = []
            layer_position_from_top = layer.offset[0]
            layer_position_from_left = layer.offset[1]
            if image.size > 0:
                layer_output_path = os.path.join(output_dir, f"{layer.name}.png")  # Save as PNG
                if not os.path.exists(layer_output_path):
                    pyplot.imsave(layer_output_path, image, cmap='gray' if image.ndim == 2 else None)
                layer_width, layer_height = None, None
                for channel in layer.channels:
                    channel_data = np.array(channel.data)
                    if layer_width is None and layer_height is None:
                        layer_height, layer_width = channel_data.shape
                        layers_info.append({
                            'name': layer.name,
                            'path': layer_output_path,

                            'layer_position_from_top': layer_position_from_top,  # Add most common colors
                            'layer_position_from_left': layer_position_from_left,  # Add most common colors
                        })


            else:
                print(f'Layer {layer.name!r} image size is zero')
    return layers_info


def extractColors():
    print("testing")

def extractColors():
    print("testing")

def single_layer_color_picker(request):
    tiff_file = request.FILES['tiff_file']
    # print(tiff_file)
    file_path = os.path.join('media', tiff_file.name)
    # print(file_path)
    with open(file_path, 'wb+') as destination:
        for chunk in tiff_file.chunks():
            destination.write(chunk)

    # Process the TIFF file

    layers = extract_layers(file_path, 'media/output/'+tiff_file.name)

    return render(request, 'single_layers.html', {'layers': layers})
    # return render(request, "layer_color_picker.html")