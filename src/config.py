import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env')


@dataclass
class Settings:
    database_url: str = field(default_factory=lambda: os.getenv('DATABASE_URL', f'sqlite:///{ROOT / "data/processed/copilot.db"}'))
    read_database_url: str = field(default_factory=lambda: os.getenv('READ_DATABASE_URL', ''))
    audit_database_url: str = field(default_factory=lambda: os.getenv('AUDIT_DATABASE_URL', ''))
    artifacts: Path = field(default_factory=lambda: Path(os.getenv('ARTIFACTS_DIR', str(ROOT / 'models'))))
    documents: Path = ROOT / 'documents'
    retrieval_mode: str = field(default_factory=lambda: os.getenv('RETRIEVAL_MODE', 'lexical'))
    llm_enabled: bool = field(default_factory=lambda: os.getenv('LLM_ENABLED', 'false').lower() == 'true')
    openai_model: str = field(default_factory=lambda: os.getenv('OPENAI_MODEL', ''))
