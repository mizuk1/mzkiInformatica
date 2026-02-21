"""Load environment variables from Django project .env for LangChain/OpenAI integration."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the Django project root
# Path: /home/thiag/projects/poe2-mybot/mzki/mzkiInformatica/.env
# File: /home/thiag/projects/poe2-mybot/mzki/mzkiInformatica/mzkiInformatica/core/my_rag/src/__init__.py
# Need 5 parent levels to go up
project_root_env = Path(__file__).parent.parent.parent.parent.parent / '.env'
if project_root_env.exists():
    load_dotenv(project_root_env, override=True)
