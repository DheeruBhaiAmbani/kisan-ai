import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

load_dotenv() # Load env variables from .env

BASE_DIR = Path(__file__).resolve().parent.parent

# --- Database ---
# For Supabase PostgreSQL
DATABASE_URL = os.environ.get('DATABASE_URL')
DATABASES = {
    'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
}

# --- General Settings ---
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '.render.com'] # Adjust for Render

# --- Installed Apps ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'users',       # Your custom user app
    'chatbot',     # Your chatbot app
    'marketplace', # Your marketplace app
    # 'whitenoise.runserver_nostatic', # For production static files on Render
    # 'sslserver', # For local HTTPS if needed
    'corsheaders', # If you use separate frontend, but here it's integrated
]

AUTH_USER_MODEL = 'users.User' # Important for custom user model

# --- Static files for Render/Whitenoise ---
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'
# STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage' # For production

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# --- API Keys ---
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY')
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') # For LangChain integration

# --- CORS Headers (if needed) ---
CORS_ALLOW_ALL_ORIGINS = True # Be more restrictive in production