echo off
echo. Default is to Convert all .md files in current directory
echo. Options:
echo. -f document.md           # Convert specific file               
echo. -o /path/to/output       # Specify output directory            
echo. -v --force               # Verbose mode with overwrite         
echo. -d /path/to/markdown     # Process files in specific directory 
echo. 
python C:\Scripts\md_to_docx.py %1 %2 %3 %4 %5 %6
pause

