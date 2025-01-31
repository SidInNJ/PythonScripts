import os
from PyPDF2 import PdfMerger

def combine_pdfs(folder_path, output_filename="combined.pdf"):
    """
    Combines all PDFs in a specified folder into a single PDF.
    
    Parameters:
        folder_path (str): The path to the folder containing the PDF files.
        output_filename (str): The name of the output combined PDF file.
    
    Returns:
        str: The path to the combined PDF.
    """
    # Create a PdfMerger object
    merger = PdfMerger()

    # Get a sorted list of PDF files in the folder
    pdf_files = sorted(
        [f for f in os.listdir(folder_path) if f.endswith('.pdf')],
        key=lambda x: x.lower()  # Sort case-insensitively
    )

    if not pdf_files:
        print("No PDF files found in the specified folder.")
        return None

    # Add each PDF file to the merger
    for pdf in pdf_files:
        pdf_path = os.path.join(folder_path, pdf)
        print(f"Adding: {pdf_path}")
        merger.append(pdf_path)

    # Define the output file path
    output_path = os.path.join(folder_path, output_filename)

    # Write the combined PDF to the output file
    merger.write(output_path)
    merger.close()

    print(f"Combined PDF saved as: {output_path}")
    return output_path

# Example usage
if __name__ == "__main__":
    folder_path = input("Enter the folder path containing PDFs: ").strip()
    output_filename = input("Enter the name for the combined PDF (default: combined.pdf): ").strip() or "combined.pdf"
    combine_pdfs(folder_path, output_filename)

