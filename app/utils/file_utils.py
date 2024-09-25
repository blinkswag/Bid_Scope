# ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
# MAX_CONTENT_LENGTH = 512 * 1024 * 1024

# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def validate_file(file):
#     if not allowed_file(file.filename):
#         return False, f'File type not allowed: {file.filename}'
#     if file.content_length > MAX_CONTENT_LENGTH:
#         return False, f'File too large: {file.filename} (max allowed is {MAX_CONTENT_LENGTH / (1024 * 1024)} MB)'
#     return True, ''
import os

ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_CONTENT_LENGTH = 512 * 1024 * 1024  # 512 MB

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    # Check if the file extension is allowed
    if not allowed_file(file.filename):
        return False, f'Invalid file format: {file.filename}. Only PDF, DOCX, and TXT files are allowed.'
    
    # Check the file size manually
    file.seek(0, os.SEEK_END)  # Move pointer to end of file
    file_size = file.tell()  # Get file size in bytes
    file.seek(0)  # Reset file pointer to the beginning

    if file_size > MAX_CONTENT_LENGTH:  # If file size is larger than 512MB
        return False, f'File too large: {file.filename} (max allowed size is {MAX_CONTENT_LENGTH / (1024 * 1024)} MB)'

    return True, ''

