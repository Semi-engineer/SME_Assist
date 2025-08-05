# File: pdf_generator.py
import os
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML, CSS
from datetime import datetime
from app_config import TEMPLATES_DIR

def create_quote_pdf(quote_data, output_path):
    # --- ใช้ TEMPLATES_DIR ที่ import เข้ามา ---
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template('quote_template.html')

    quote_data['date'] = datetime.now().strftime("%d/%m/%Y")
    quote_data['quote_id'] = f"QT-{datetime.now().strftime('%Y%m%d-%H%M')}"
    
    html_out = template.render(quote_data)
    
    css_path = os.path.join(TEMPLATES_DIR, 'style.css')
    HTML(string=html_out).write_pdf(output_path, stylesheets=[CSS(css_path)])
    
    print(f"PDF successfully generated at: {output_path}")