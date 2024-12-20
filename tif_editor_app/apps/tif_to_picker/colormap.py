import numpy as np
from PIL import Image
import io
import base64
from colormath.color_objects import LabColor, sRGBColor, HSVColor
from colormath.color_conversions import convert_color
from collections import defaultdict

def rgb_to_lab_batch(rgb_array):
    rgb_normalized = rgb_array.astype(np.float32) / 255.0
    if len(rgb_normalized.shape) == 1:
        rgb_normalized = rgb_normalized.reshape(1, -1)
    
    lab_list = [convert_color(sRGBColor(r, g, b), LabColor) 
                for r, g, b in rgb_normalized]
    
    lab_array = np.array([[lab.lab_l, lab.lab_a, lab.lab_b] 
                         for lab in lab_list])
    return lab_array

def rgb_to_hsv(rgb):
    r, g, b = rgb[0]/255.0, rgb[1]/255.0, rgb[2]/255.0
    max_val = max(r, g, b)
    min_val = min(r, g, b)
    diff = max_val - min_val

    if max_val == min_val:
        h = 0
    elif max_val == r:
        h = (60 * ((g-b)/diff) + 360) % 360
    elif max_val == g:
        h = (60 * ((b-r)/diff) + 120) % 360
    else:
        h = (60 * ((r-g)/diff) + 240) % 360

    s = 0 if max_val == 0 else (diff / max_val)
    v = max_val
    
    return np.array([h, s, v])

def hsv_to_rgb(hsv):
    h, s, v = hsv[0], hsv[1], hsv[2]
    
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c

    if 0 <= h < 60:
        r, g, b = c, x, 0
    elif 60 <= h < 120:
        r, g, b = x, c, 0
    elif 120 <= h < 180:
        r, g, b = 0, c, x
    elif 180 <= h < 240:
        r, g, b = 0, x, c
    elif 240 <= h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x

    return np.array([
        int((r + m) * 255),
        int((g + m) * 255),
        int((b + m) * 255)
    ])

def get_dominant_colors(pixels, n_colors=5):
    pixels = pixels.reshape(-1, 3)
    pixels = np.round(pixels / 10) * 10  # Quantize colors
    unique, counts = np.unique(pixels, axis=0, return_counts=True)
    sorted_indices = np.argsort(-counts)
    return unique[sorted_indices[:n_colors]].astype(int)

def get_color_mapping_django(image_data):
    if isinstance(image_data, str) and image_data.startswith('data:image/'):
        image_data = image_data.split(',')[1]
        image_bytes = base64.b64decode(image_data)
        img = Image.open(io.BytesIO(image_bytes))
    else:
        img = image_data

    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    data = np.array(img)
    
    # Create mask for valid pixels
    alpha_mask = data[..., 3] > 128
    rgb_data = data[..., :3]
    valid_pixels = rgb_data[alpha_mask]
    
    if len(valid_pixels) == 0:
        return {'baseColor': [0, 0, 0], 'shades': []}
    
    # Get unique colors
    unique_colors = np.unique(valid_pixels, axis=0)
    
    # Convert all unique colors to Lab space
    lab_colors = rgb_to_lab_batch(unique_colors)
    
    shades = []
    for color, lab in zip(unique_colors, lab_colors):
        shades.append({
            'original': color.tolist(),
            'lab': lab.tolist()
        })
    
    # Find the most dominant color as base color
    base_color = get_dominant_colors(valid_pixels, n_colors=1)[0]
    
    return {
        'baseColor': base_color.tolist(),
        'shades': shades
    }

def create_color_transform(original_color, target_color):
    original_hsv = rgb_to_hsv(original_color)
    target_hsv = rgb_to_hsv(target_color)
    
    # Calculate the hue difference
    h_diff = target_hsv[0] - original_hsv[0]
    
    # Calculate saturation ratio with better preservation of shades
    base_saturation = max(0.0001, original_hsv[1])
    target_saturation = target_hsv[1]
    s_ratio = (0.7 * target_saturation / base_saturation) + 0.3
    
    # Calculate value/brightness ratio to maintain shading
    v_ratio = target_hsv[2] / max(0.0001, original_hsv[2])
    
    return h_diff, s_ratio, v_ratio

def apply_color_transform(color, h_diff, s_ratio, v_ratio):
    hsv = rgb_to_hsv(color)
    
    # Apply transformations
    new_h = (hsv[0] + h_diff) % 360
    
    # Modified saturation handling
    original_s = hsv[1]
    if original_s < 0.2:
        # For very unsaturated areas, blend with target saturation
        new_s = original_s * 0.8 + (original_s * s_ratio) * 0.2
    else:
        # For saturated areas, maintain more of the target characteristics
        new_s = min(1.0, original_s * s_ratio)
    
    # Modified value/brightness handling to maintain shading
    original_v = hsv[2]
    new_v = min(1.0, original_v * (v_ratio * 0.5 + 0.5))
    
    return hsv_to_rgb([new_h, new_s, new_v])

def apply_color_mapping_django(image_data, color_mapping, target_color):
    if isinstance(image_data, str) and image_data.startswith('data:image/'):
        image_data = image_data.split(',')[1]
    
    image_bytes = base64.b64decode(image_data)
    img = Image.open(io.BytesIO(image_bytes))
    
    if img.mode != 'RGBA':
        img = img.convert('RGBA')
    
    img_array = np.array(img)
    
    # Create the color transform based on base color
    h_diff, s_ratio, v_ratio = create_color_transform(
        np.array(color_mapping['baseColor']), 
        np.array(target_color)
    )
    
    # Create color mapping dictionary
    color_map = {}
    for shade in color_mapping['shades']:
        original = tuple(int(x) for x in shade['original'])
        new_color = apply_color_transform(
            np.array(original), 
            h_diff, 
            s_ratio, 
            v_ratio
        )
        color_map[original] = new_color.tolist()
    
    # Apply color mapping
    height, width = img_array.shape[:2]
    rgb_view = img_array[..., :3]
    alpha_mask = img_array[..., 3] > 128
    
    # Create a view of the RGB pixels
    rgb_pixels = rgb_view[alpha_mask]
    
    # Create output array
    new_pixels = np.zeros_like(rgb_pixels)
    
    # For each unique color in the input, apply the transformation
    for i, pixel in enumerate(rgb_pixels):
        pixel_tuple = tuple(pixel)
        if pixel_tuple in color_map:
            new_pixels[i] = color_map[pixel_tuple]
        else:
            new_pixels[i] = pixel
    
    # Update the original array
    rgb_view[alpha_mask] = new_pixels
    
    # Create new image
    modified_img = Image.fromarray(img_array)
    
    # Convert to base64
    buffered = io.BytesIO()
    modified_img.save(buffered, format="PNG")
    modified_image_base64 = base64.b64encode(buffered.getvalue()).decode()
    
    return f'data:image/png;base64,{modified_image_base64}'