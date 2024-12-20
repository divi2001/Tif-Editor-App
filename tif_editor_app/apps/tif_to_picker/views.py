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
from sklearn.cluster import KMeans
import colorsys
from typing import Dict, List, Optional
import webcolors
from colorsys import rgb_to_hls
import base64
import zlib
import piexif
import imagecodecs
from PIL import ImageOps
import cv2
import logging
from .getcolors import analyze_image_colors
from io import BytesIO
from .colormap import apply_color_mapping_django,get_color_mapping_django
logger = logging.getLogger(__name__)

from django.shortcuts import render
from apps.mainadmin.models import InspirationPDF

def inspiration_view(request):
    pdfs = InspirationPDF.objects.all().order_by('-created_at')
    pdfs_data = [{
        'id': pdf.id,
        'title': pdf.title,
        'preview_image': pdf.preview_image.url if pdf.preview_image else None,
        'pdf_url': pdf.pdf_file.url if pdf.pdf_file else None,
        'likes_count': pdf.likes_count,
        'created_at': pdf.created_at.strftime('%Y-%m-%d')
    } for pdf in pdfs]
    
    return JsonResponse({'pdfs': pdfs_data})

@csrf_exempt
def apply_color(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        image_data = data.get('imageData')
        target_color = data.get('targetColor')
        
        # First get the color mapping
        color_mapping = get_color_mapping_django(image_data)
        
        # Then apply the color mapping
        modified_image = apply_color_mapping_django(
            image_data,
            color_mapping,
            target_color
        )
        
        return JsonResponse({
            'success': True,
            'modifiedImage': modified_image,
            'colorMapping': color_mapping
        })

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

def advanced_compress_png(image_array, output_path, quality_threshold=0.95):
    """
    Advanced compression using multiple techniques and selecting the best result
    """
    try:
        # Convert numpy array to PIL Image
        if image_array.ndim == 2:
            img = Image.fromarray(np.uint8(image_array * 255), 'L')
        else:
            img = Image.fromarray(np.uint8(image_array * 255), 'RGB')

        # Original size
        temp_buffer = BytesIO()
        img.save(temp_buffer, format='PNG')
        original_size = temp_buffer.tell()
        best_size = original_size
        best_method = None
        best_data = None

        # Method 1: PIL's built-in optimization
        temp_buffer = BytesIO()
        img.save(temp_buffer, 
                format='PNG',
                optimize=True,
                compress_level=9)
        size1 = temp_buffer.tell()
        if size1 < best_size:
            best_size = size1
            best_method = "PIL"
            best_data = temp_buffer.getvalue()

        # Method 2: Remove metadata and convert to optimized palette
        img_no_meta = ImageOps.exif_transpose(img)
        if img_no_meta.mode in ['RGB', 'RGBA']:
            try:
                img_no_meta = img_no_meta.quantize(colors=256, method=2)
            except Exception as e:
                print(f"Quantization failed: {e}")

        temp_buffer = BytesIO()
        img_no_meta.save(temp_buffer,
                        format='PNG',
                        optimize=True,
                        compress_level=9)
        size2 = temp_buffer.tell()
        if size2 < best_size:
            best_size = size2
            best_method = "Palette"
            best_data = temp_buffer.getvalue()

        # Method 3: OpenCV compression
        if image_array.ndim == 3:
            # Convert to BGR for OpenCV
            cv_img = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
        else:
            cv_img = image_array

        encode_param = [cv2.IMWRITE_PNG_COMPRESSION, 9]
        _, encoded = cv2.imencode('.png', cv_img, encode_param)
        size3 = len(encoded)
        if size3 < best_size:
            best_size = size3
            best_method = "OpenCV"
            best_data = encoded.tobytes()

        # Method 4: Using imagecodecs for additional compression
        try:
            compressed = imagecodecs.png_encode(image_array, level=9)
            size4 = len(compressed)
            if size4 < best_size:
                best_size = size4
                best_method = "imagecodecs"
                best_data = compressed
        except Exception as e:
            print(f"imagecodecs compression failed: {e}")

        # Save the best result
        if best_data and best_size < original_size:
            with open(output_path, 'wb') as f:
                f.write(best_data)
            compression_ratio = (original_size - best_size) / original_size * 100
            print(f"Best compression achieved with {best_method}: {compression_ratio:.1f}% reduction")
        else:
            # If no better compression found, save with default optimization
            img.save(output_path, format='PNG', optimize=True, compress_level=9)
            
        return best_size
    except Exception as e:
        print(f"Error in advanced compression: {str(e)}")
        return None

def extract_layers(file_path, output_dir):
    isd = TiffImageSourceData.fromtiff(file_path)

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    layers_info = []
    
    if isd.layers:
        for layer in isd.layers:
            try:
                image = layer.asarray()
                layer_position_from_top = layer.offset[0]
                layer_position_from_left = layer.offset[1]
                
                if image.size > 0:
                    # Check if image contains transparency
                    has_transparency = (image.shape[-1] == 4) if len(image.shape) > 2 else False
                    
                    layer_output_path = os.path.join(output_dir, f"{layer.name}.png")
                    
                    if not os.path.exists(layer_output_path):
                        original_size = image.nbytes
                        
                        # Pre-process image if possible
                        if not has_transparency:
                            # Reduce color depth if possible
                            if image.ndim == 3:
                                image = np.uint8(image * 255)
                                # Convert to grayscale if RGB channels are similar
                                r, g, b = image[:,:,0], image[:,:,1], image[:,:,2]
                                if np.allclose(r, g, rtol=0.05) and np.allclose(g, b, rtol=0.05):
                                    image = np.mean(image, axis=2).astype(np.uint8)

                        compressed_size = advanced_compress_png(image, layer_output_path)
                        
                        if compressed_size:
                            compression_ratio = (original_size - compressed_size) / original_size * 100
                            print(f"Layer {layer.name}: Compressed from {original_size/1024:.2f}KB to {compressed_size/1024:.2f}KB ({compression_ratio:.1f}% reduction)")
                    
                    layer_width, layer_height = None, None
                    for channel in layer.channels:
                        channel_data = np.array(channel.data)
                        if layer_width is None and layer_height is None:
                            layer_height, layer_width = channel_data.shape
                            layers_info.append({
                                'name': layer.name,
                                'path': layer_output_path,
                                'layer_position_from_top': layer_position_from_top,
                                'layer_position_from_left': layer_position_from_left,
                            })
                else:
                    print(f'Layer {layer.name!r} image size is zero')
                    
            except Exception as e:
                print(f"Error processing layer {layer.name}: {str(e)}")
                continue

    return layers_info

# Optional: Add a function to check file sizes
def get_file_size_mb(file_path):
    """Get file size in MB"""
    return os.path.getsize(file_path) / (1024 * 1024)

# Optional: Add batch compression for existing files
def compress_existing_files(directory):
    """Compress all existing PNG files in directory"""
    for filename in os.path.listdir(directory):
        if filename.endswith('.png'):
            file_path = os.path.join(directory, filename)
            original_size = get_file_size_mb(file_path)
            
            # Create temporary path for new compressed file
            temp_path = os.path.join(directory, f"temp_{filename}")
            
            # Open and recompress
            try:
                with Image.open(file_path) as img:
                    img.save(temp_path, 
                           format='PNG',
                           optimize=True,
                           compress_level=9,
                           include_color_table=False)
                
                new_size = get_file_size_mb(temp_path)
                
                # Replace original with compressed version if smaller
                if new_size < original_size:
                    os.replace(temp_path, file_path)
                    print(f"Compressed {filename}: {original_size:.2f}MB → {new_size:.2f}MB")
                else:
                    os.remove(temp_path)
                    print(f"Kept original {filename} (already optimized)")
                    
            except Exception as e:
                print(f"Error compressing {filename}: {str(e)}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)

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