ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}
MAX_CONTENT_LENGTH = 32 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def validate_file(file):
    if not allowed_file(file.filename):
        return False, f'File type not allowed: {file.filename}'
    if file.content_length > MAX_CONTENT_LENGTH:
        return False, f'File too large: {file.filename} (max allowed is {MAX_CONTENT_LENGTH / (1024 * 1024)} MB)'
    return True, ''
