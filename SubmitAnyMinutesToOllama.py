#!/usr/bin/env python3
"""
Meeting Minutes Processor for Ollama - Enhanced Version

This script processes meeting minutes in various formats (TXT, ODT, DOCX) using the Mistral model in Ollama.
It converts the input file to plain text if needed, then transforms raw meeting notes into 
a well-formatted document with an executive summary.

Usage:
    python SubmitAnyMinutesToOllama.py path/to/your/meeting_minutes.[txt|odt|docx]

Requirements:
    - Ollama installed with mistral:7b-instruct-q5_K_M model pulled
    - Python 3.6+
    - python-docx (for DOCX files)
    - odfpy (for ODT files)
"""

import subprocess
import os
import sys
import argparse
import re
from datetime import datetime

# For file format conversions
try:
    import docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    print("Warning: python-docx not installed. DOCX conversion will not be available.")
    print("Install with: pip install python-docx")

try:
    from odf import text, teletype
    from odf.opendocument import load
    ODT_AVAILABLE = True
except ImportError:
    ODT_AVAILABLE = False
    print("Warning: odfpy not installed. ODT conversion will not be available.")
    print("Install with: pip install odfpy")


def clean_text(text_content):
    """Clean text content by removing illegal characters and normalizing line endings."""
    # Replace any non-printable characters
    cleaned_text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text_content)
    
    # Normalize line endings
    cleaned_text = cleaned_text.replace('\r\n', '\n').replace('\r', '\n')
    
    # Remove any UTF-8 BOM if present
    if cleaned_text.startswith('\ufeff'):
        cleaned_text = cleaned_text[1:]
    
    return cleaned_text


def convert_docx_to_text(docx_path):
    """Convert a DOCX file to plain text."""
    if not DOCX_AVAILABLE:
        print("Error: python-docx is required for DOCX conversion.")
        return None
    
    try:
        doc = docx.Document(docx_path)
        full_text = []
        for para in doc.paragraphs:
            full_text.append(para.text)
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error converting DOCX file: {e}")
        return None


def convert_odt_to_text(odt_path):
    """Convert an ODT file to plain text."""
    if not ODT_AVAILABLE:
        print("Error: odfpy is required for ODT conversion.")
        return None
    
    try:
        textdoc = load(odt_path)
        allparas = textdoc.getElementsByType(text.P)
        full_text = []
        for para in allparas:
            full_text.append(teletype.extractText(para))
        return '\n'.join(full_text)
    except Exception as e:
        print(f"Error converting ODT file: {e}")
        return None


def convert_to_text(input_file_path):
    """Convert the input file to plain text based on its extension."""
    file_ext = os.path.splitext(input_file_path)[1].lower()
    
    if file_ext == '.txt':
        try:
            with open(input_file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return clean_text(content)
        except UnicodeDecodeError:
            # Try with a different encoding if UTF-8 fails
            try:
                with open(input_file_path, 'r', encoding='latin-1') as file:
                    content = file.read()
                return clean_text(content)
            except Exception as e:
                print(f"Error reading text file with latin-1 encoding: {e}")
                return None
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None
    
    elif file_ext == '.docx':
        return convert_docx_to_text(input_file_path)
    
    elif file_ext == '.odt':
        return convert_odt_to_text(input_file_path)
    
    else:
        print(f"Unsupported file format: {file_ext}")
        print("Supported formats: .txt, .docx, .odt")
        return None


def process_meeting_minutes(text_content, model="mistral:7b-instruct-q5_K_M", original_filename=""):
    """Process meeting minutes using Ollama with the specified model."""
    
    print(f"Processing content: {len(text_content)} characters")
    
    # Prepare the prompt
    prompt = """
    I need you to transform these raw meeting minutes into a well-organized document with:

    1. An executive summary (max 250 words) at the top highlighting:
       - Key decisions made
       - Critical action items
       - Major discussion points
    
    2. The main content organized into clearly defined sections:
       - Attendees
       - Agenda items with discussion points
       - Decisions reached (highlighted)
       - Action items (with owner and deadline if mentioned)
    
    Format the content to be highly readable with appropriate headers, bullet points, and whitespace.

    Here are the meeting minutes:

    """ + text_content
    
    print("Sending to Ollama for processing...")
    
    # Run ollama with the prepared prompt
    try:
        cmd = ["ollama", "run", model, prompt]
        # Set encoding explicitly to UTF-8 and handle errors
        result = subprocess.run(cmd, capture_output=True, text=False)
        
        if result.returncode != 0:
            stderr_text = result.stderr.decode('utf-8', errors='replace')
            print(f"Error running Ollama: {stderr_text}")
            return None
        
        # Safely decode stdout with error handling
        stdout_text = result.stdout.decode('utf-8', errors='replace')
            
    except Exception as e:
        print(f"Error executing Ollama: {e}")
        return None
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if original_filename:
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
    else:
        base_name = "meeting_minutes"
    output_file_path = f"{base_name}_formatted_{timestamp}.txt"
    
    # Save the result
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(stdout_text)
        print(f"Processed meeting minutes saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")
        return None
    
    return output_file_path


def process_large_meeting_minutes(text_content, model="mistral:7b-instruct-q5_K_M", max_chunk_size=3800, original_filename=""):
    """Process large meeting minutes by breaking them into chunks."""
    
    print(f"Processing large content: {len(text_content)} characters")
    
    # Check if we need to chunk the content
    if len(text_content) <= max_chunk_size:
        print("Content is small enough to process in one go.")
        return process_meeting_minutes(text_content, model, original_filename)
    
    # Split by paragraphs and create chunks
    paragraphs = text_content.split('\n\n')
    chunks = []
    current_chunk = ""
    
    for paragraph in paragraphs:
        if len(current_chunk) + len(paragraph) < max_chunk_size:
            current_chunk += paragraph + "\n\n"
        else:
            chunks.append(current_chunk)
            current_chunk = paragraph + "\n\n"
    
    if current_chunk:
        chunks.append(current_chunk)
    
    print(f"Split content into {len(chunks)} chunks for processing")
    
    # Process each chunk
    processed_chunks = []
    for i, chunk in enumerate(chunks):
        print(f"Processing chunk {i+1}/{len(chunks)}...")
        
        # Different prompt for first chunk
        if i == 0:
            prompt = """
            Transform these meeting minutes into a well-organized document. 
            Start with an executive summary highlighting key decisions and action items.
            This is the first part of the meeting minutes:
            
            """ + chunk
        else:
            prompt = f"""
            Continue formatting the meeting minutes. This is part {i+1} of the meeting:
            
            """ + chunk
        
        try:
            cmd = ["ollama", "run", model, prompt]
            result = subprocess.run(cmd, capture_output=True, text=False)
            # Safely decode stdout with error handling
            stdout_text = result.stdout.decode('utf-8', errors='replace')
            processed_chunks.append(stdout_text)
        except Exception as e:
            print(f"Error processing chunk {i+1}: {e}")
            continue
    
    # Final summarization pass if we have multiple chunks
    if len(chunks) > 1:
        print("Creating final executive summary...")
        final_prompt = """
        Based on all the meeting content processed, create a final executive summary (max 250 words) 
        highlighting the most important decisions and action items:
        
        Key points from the meeting:
        """ + "\n\n".join(processed_chunks[:3])  # Send first few chunks as context
        
        try:
            cmd = ["ollama", "run", model, final_prompt]
            result = subprocess.run(cmd, capture_output=True, text=False)
            # Safely decode stdout with error handling
            summary = result.stdout.decode('utf-8', errors='replace')
            
            # Combine everything
            final_output = summary + "\n\n" + "\n\n".join(processed_chunks)
        except Exception as e:
            print(f"Error creating final summary: {e}")
            final_output = "\n\n".join(processed_chunks)
    else:
        final_output = processed_chunks[0]
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if original_filename:
        base_name = os.path.splitext(os.path.basename(original_filename))[0]
    else:
        base_name = "meeting_minutes"
    output_file_path = f"{base_name}_formatted_{timestamp}.txt"
    
    # Save the result
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(final_output)
        print(f"Processed meeting minutes saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")
        return None
    
    return output_file_path


def main():
    """Main function to parse arguments and process the meeting minutes."""
    parser = argparse.ArgumentParser(description='Process meeting minutes using Ollama.')
    parser.add_argument('input_file', help='Path to the meeting minutes file (TXT, ODT, or DOCX)')
    parser.add_argument('--model', default='mistral:7b-instruct-q5_K_M', 
                        help='Ollama model to use (default: mistral:7b-instruct-q5_K_M)')
    parser.add_argument('--large', action='store_true', 
                        help='Enable processing for large files by chunking')
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.input_file):
        print(f"Error: File {args.input_file} not found.")
        return
    
    # Convert the file to text
    text_content = convert_to_text(args.input_file)
    
    if text_content is None:
        print("Failed to convert file to text. Exiting.")
        return
    
    # Process the text content
    if args.large:
        process_large_meeting_minutes(text_content, args.model, original_filename=args.input_file)
    else:
        process_meeting_minutes(text_content, args.model, original_filename=args.input_file)


if __name__ == "__main__":
    main()
