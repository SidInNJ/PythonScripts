from PIL import Image
import os
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
import math
from collections import defaultdict

def process_images(input_dir, output_pdf, images_per_page=20, target_size=(400, 300)):
    """
    Combine multiple resized images onto PDF pages with captions.
    Sort by first name, except group same last names together.
    """
    
    # Get image files and parse names
    image_files = []
    last_name_groups = defaultdict(list)
    singles = []
    
    for f in os.listdir(input_dir):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
            base_name = os.path.splitext(f)[0]
            try:
                first_name, last_name = base_name.split(' ', 1)
                last_name_groups[last_name].append((f, first_name))
            except ValueError:
                singles.append((f, base_name))
    
    # Process groups and singles
    final_files = []
    
    # Add singles sorted by first name
    singles.sort(key=lambda x: x[1])
    
    # Process last name groups
    grouped = []
    for last_name, group in last_name_groups.items():
        if len(group) > 1:  # Only group if multiple with same last name
            group.sort(key=lambda x: x[1])  # Sort by first name within group
            grouped.extend(group)
        else:
            singles.extend(group)  # Add to singles if only one with that last name
            
    # Sort singles by first name
    singles.sort(key=lambda x: x[1])
    
    # Combine lists: singles first (sorted by first name), then grouped families
    final_files = [x[0] for x in singles] + [x[0] for x in grouped]
    
    # Create PDF
    c = canvas.Canvas(output_pdf, pagesize=letter)
    width, height = letter
    
    # Calculate grid layout
    cols = math.floor(math.sqrt(images_per_page))
    rows = math.ceil(images_per_page / cols)
    
    # Calculate image size and spacing
    img_width = width * 0.8 / cols
    img_height = height * 0.8 / rows
    x_spacing = width * 0.1 / (cols + 1)
    y_spacing = height * 0.1 / (rows + 1)
    
    current_image = 0
    while current_image < len(final_files):
        y = height - y_spacing - img_height
        
        for row in range(rows):
            x = x_spacing
            
            for col in range(cols):
                if current_image >= len(final_files):
                    break
                    
                try:
                    img_file = final_files[current_image]
                    
                    # Open and resize image
                    img = Image.open(os.path.join(input_dir, img_file))
                    img = img.convert('RGB')
                    img.thumbnail(target_size, Image.Resampling.LANCZOS)
                    
                    # Save temporary resized image
                    temp_path = f"temp_resize_{current_image}.jpg"
                    img.save(temp_path)
                    
                    # Add image to PDF
                    c.drawImage(temp_path, x, y, 
                              width=img_width, height=img_height,
                              preserveAspectRatio=True)
                    
                    # Add caption
                    caption = os.path.splitext(img_file)[0]
                    c.setFont("Helvetica", 8)
                    c.drawCentredString(x + img_width/2, y - 10, caption)
                    
                    os.remove(temp_path)
                    
                except Exception as e:
                    print(f"Error processing {img_file}: {str(e)}")
                
                x += img_width + x_spacing
                current_image += 1
            
            y -= img_height + y_spacing + 15
            
            if current_image >= len(final_files):
                break
                
        c.showPage()
    
    c.save()

if __name__ == "__main__":
    process_images("./images", "GuatemalaTeam2025.pdf")
