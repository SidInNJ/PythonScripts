#!/usr/bin/env python3
"""
Meeting Minutes Processor for Ollama

This script processes meeting minutes in text format using the Mistral model in Ollama.
It transforms raw meeting notes into a well-formatted document with an executive summary.

Usage:
    python meeting_minutes_processor.py path/to/your/meeting_minutes.txt

Requirements:
    - Ollama installed with mistral:7b-instruct-q5_K_M model pulled
    - Python 3.6+
"""

import subprocess
import os
import sys
import argparse
from datetime import datetime

def process_meeting_minutes(input_file_path, model="mistral:7b-instruct-q5_K_M"):
    """Process meeting minutes using Ollama with the specified model."""
    
    print(f"Processing file: {input_file_path}")
    
    # Check if file exists
    if not os.path.exists(input_file_path):
        print(f"Error: File {input_file_path} not found.")
        return None
    
    # Read the content of the text file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            meeting_content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    print(f"File loaded. Content length: {len(meeting_content)} characters")
    
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

    """ + meeting_content
    
    print("Sending to Ollama for processing...")
    
    # Run ollama with the prepared prompt
    try:
        cmd = ["ollama", "run", model, prompt]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error running Ollama: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"Error executing Ollama: {e}")
        return None
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
    output_file_path = f"{base_name}_formatted_{timestamp}.txt"
    
    # Save the result
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            file.write(result.stdout)
        print(f"Processed meeting minutes saved to {output_file_path}")
    except Exception as e:
        print(f"Error saving output file: {e}")
        return None
    
    return output_file_path

def process_large_meeting_minutes(input_file_path, model="mistral:7b-instruct-q5_K_M", max_chunk_size=3800):
    """Process large meeting minutes by breaking them into chunks."""
    
    print(f"Processing large file: {input_file_path}")
    
    # Read the content of the text file
    try:
        with open(input_file_path, 'r', encoding='utf-8') as file:
            meeting_content = file.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        return None
    
    print(f"File loaded. Content length: {len(meeting_content)} characters")
    
    # Check if we need to chunk the content
    if len(meeting_content) <= max_chunk_size:
        print("Content is small enough to process in one go.")
        return process_meeting_minutes(input_file_path, model)
    
    # Split by paragraphs and create chunks
    paragraphs = meeting_content.split('\n\n')
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
            result = subprocess.run(cmd, capture_output=True, text=True)
            processed_chunks.append(result.stdout)
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
            summary = subprocess.run(cmd, capture_output=True, text=True).stdout
            
            # Combine everything
            final_output = summary + "\n\n" + "\n\n".join(processed_chunks)
        except Exception as e:
            print(f"Error creating final summary: {e}")
            final_output = "\n\n".join(processed_chunks)
    else:
        final_output = processed_chunks[0]
    
    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = os.path.splitext(os.path.basename(input_file_path))[0]
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
    parser.add_argument('input_file', help='Path to the meeting minutes text file')
    parser.add_argument('--model', default='mistral:7b-instruct-q5_K_M', 
                        help='Ollama model to use (default: mistral:7b-instruct-q5_K_M)')
    parser.add_argument('--large', action='store_true', 
                        help='Enable processing for large files by chunking')
    args = parser.parse_args()
    
    if args.large:
        process_large_meeting_minutes(args.input_file, args.model)
    else:
        process_meeting_minutes(args.input_file, args.model)

if __name__ == "__main__":
    main()
