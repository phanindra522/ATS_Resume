#!/usr/bin/env python3
"""
Convert Markdown Design Document to Word Format
"""

import re
from docx import Document
from docx.shared import Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def convert_markdown_to_word():
    """Convert the markdown design document to Word format"""
    
    # Read the markdown file
    try:
        with open('../ATS_Resume_Design_Document.md', 'r', encoding='utf-8') as f:
            md_content = f.read()
    except FileNotFoundError:
        print("Error: ATS_Resume_Design_Document.md not found")
        return False
    
    # Create a new Word document
    doc = Document()
    
    # Add title
    title = doc.add_heading('ATS Resume Scoring Assistant - Design Document', 0)
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add document info
    doc.add_paragraph('Document Version: 1.0')
    doc.add_paragraph('Last Updated: January 2024')
    doc.add_paragraph('Project: ATS Resume Scoring Assistant')
    doc.add_paragraph('')
    
    # Process content line by line
    lines = md_content.split('\n')
    in_code_block = False
    in_table = False
    
    for line in lines:
        line = line.strip()
        
        # Skip empty lines
        if not line:
            if not in_code_block and not in_table:
                doc.add_paragraph('')
            continue
        
        # Handle code blocks
        if line.startswith('```'):
            in_code_block = not in_code_block
            continue
        
        if in_code_block:
            # Add code as monospace text
            p = doc.add_paragraph(line)
            p.style = 'No Spacing'
            continue
        
        # Handle headers
        if line.startswith('#'):
            level = len(line) - len(line.lstrip('#'))
            heading_text = line.lstrip('# ').strip()
            
            # Remove table of contents markers
            if heading_text.startswith('Table of Contents'):
                continue
            
            if level == 1:
                doc.add_heading(heading_text, 1)
            elif level == 2:
                doc.add_heading(heading_text, 2)
            elif level == 3:
                doc.add_heading(heading_text, 3)
            elif level == 4:
                doc.add_heading(heading_text, 4)
            else:
                doc.add_heading(heading_text, 5)
            continue
        
        # Handle horizontal rules
        if line.startswith('---'):
            doc.add_paragraph('_' * 50)
            continue
        
        # Handle tables (simplified)
        if line.startswith('|'):
            if not in_table:
                in_table = True
                # Start table processing
                table_data = []
            
            # Clean table row
            cells = [cell.strip() for cell in line.split('|')[1:-1]]
            table_data.append(cells)
            continue
        else:
            if in_table and table_data:
                # Create table
                if len(table_data) > 1:
                    table = doc.add_table(rows=len(table_data), cols=len(table_data[0]))
                    table.style = 'Table Grid'
                    
                    for i, row_data in enumerate(table_data):
                        for j, cell_data in enumerate(row_data):
                            if j < len(table.rows[i].cells):
                                table.rows[i].cells[j].text = cell_data
                
                in_table = False
                table_data = []
        
        # Handle regular text
        if line and not line.startswith('|'):
            # Clean up markdown formatting
            clean_line = line
            
            # Remove bold formatting
            clean_line = re.sub(r'\*\*(.*?)\*\*', r'\1', clean_line)
            
            # Remove italic formatting
            clean_line = re.sub(r'\*(.*?)\*', r'\1', clean_line)
            
            # Remove code formatting
            clean_line = re.sub(r'`(.*?)`', r'\1', clean_line)
            
            # Remove links (keep text only)
            clean_line = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', clean_line)
            
            # Handle bullet points
            if clean_line.startswith('- '):
                doc.add_paragraph(clean_line[2:], style='List Bullet')
            elif clean_line.startswith('* '):
                doc.add_paragraph(clean_line[2:], style='List Bullet')
            elif clean_line.startswith('1. '):
                doc.add_paragraph(clean_line[3:], style='List Number')
            else:
                if clean_line.strip():
                    doc.add_paragraph(clean_line)
    
    # Save the document
    try:
        doc.save('../ATS_Resume_Design_Document.docx')
        print("✅ Word document created successfully: ATS_Resume_Design_Document.docx")
        return True
    except Exception as e:
        print(f"❌ Error saving Word document: {e}")
        return False

if __name__ == "__main__":
    convert_markdown_to_word()
