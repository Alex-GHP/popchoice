import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_ANON_KEY"]
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
TMDB_API_KEY = os.environ["TMDB_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
API_SECRET = os.environ["API_SECRET"]
