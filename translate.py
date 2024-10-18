import os
import fitz  
from googletrans import Translator
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io
from PIL import Image
import torch
from torchvision import models, transforms
import tempfile

def translate_text(text, src_lang='es', dest_lang='en'):
    translator = Translator()
    try:
        translation = translator.translate(text, src=src_lang, dest=dest_lang)
        print(f"Original: {text} -> Translated: {translation.text}")
        return translation.text
    except Exception as e:
        return text  


model = models.detection.maskrcnn_resnet50_fpn(weights=models.detection.MaskRCNN_ResNet50_FPN_Weights.COCO_V1)
model.eval()


transform = transforms.Compose([
    transforms.ToTensor()
])

def detect_layout(image):
    image_tensor = transform(image).unsqueeze(0)  
    with torch.no_grad():
        prediction = model(image_tensor)
    return prediction

def translate_pdf(input_path, output_path):
   
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    
    document = fitz.open(input_path)

    
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)

    
    for page_num in range(len(document)):
        page = document.load_page(page_num)
        
        blocks = page.get_text("dict")["blocks"]

       

        checkbox_blocks = []
        
        for block in blocks:
            if block['type'] == 0:  
                bbox = fitz.Rect(block['bbox'])
                page.draw_rect(bbox, color=(1, 1, 1), fill=(1, 1, 1))
            elif block['type'] == 1:  
                bbox = fitz.Rect(block['bbox'])
                checkbox_blocks.append(bbox)
        
        
        pix = page.get_pixmap()
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

      
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp_file:
            image.save(tmp_file, format='PNG')
            tmp_file_path = tmp_file.name

       
        can.drawImage(tmp_file_path, 0, 0, width=letter[0], height=letter[1])

        
        os.remove(tmp_file_path)

        for block in blocks:
            if "lines" in block:
                for line in block["lines"]:
                    translated_line = []
                    for span in line["spans"]:
                        
                        translated_text = translate_text(span["text"])
                        translated_line.append(translated_text)

                   
                    full_translated_line = ' '.join(translated_line)

                    
                    font = "Helvetica"
                    size = line["spans"][0].get("size", 12)
                    x, y = line["spans"][0]["origin"]

                    
                    adjusted_x = x
                    for checkbox in checkbox_blocks:
                        if checkbox.intersects(fitz.Rect(x, y, x + 100, y + size)):
                            adjusted_x = checkbox.x1 + 50 
                            break

                    try:
                        can.setFont(font, size)
                    except KeyError:
                        can.setFont("Helvetica", size) 

                    
                    can.drawString(adjusted_x, letter[1] - y, full_translated_line)

        can.showPage()

    can.save()

  
    packet.seek(0)

   
    new_pdf = fitz.open("pdf", packet.read())

   
    new_pdf.save(output_path)


input_path = r'C:\Users\nmana\OneDrive\Desktop\PROJECTS\translate\MEDICAL-HISTORY-FORM-SPANISH-PASADENA1.pdf'
output_path = r'C:\Users\nmana\OneDrive\Desktop\PROJECTS\translate\MEDICAL--HISTORY2.pdf'

translate_pdf(input_path, output_path)
