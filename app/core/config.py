"""Configuration settings for the application."""
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    """Application settings."""
    
    # LLM - Gemini (Primary Provider)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"  # Primary model (gemini-2.5-flash)
    # Fallback models: Tự chọn trong code (default: gemini-2.0-flash-exp, gemini-1.5-pro)
    # Có thể thay đổi trong app/services/rag_graph_service.py
    
    # LLM - Ollama (Fallback Provider, Optional)
    # Qwen2.5:7b được khuyến nghị cho tiếng Việt (hỗ trợ tốt nhất)
    # Các model khác: llama3, mistral, gemma:7b (hỗ trợ tiếng Việt kém hơn)
    OLLAMA_ENABLED: bool = True  # Enable/disable Ollama fallback (default: True cho dự án)
    OLLAMA_BASE_URL: str = "http://localhost:11434/v1"
    OLLAMA_API_KEY: str = "ollama"  # Dummy key, Ollama doesn't require real API key
    OLLAMA_MODEL: str = "qwen2.5:7b"  # Model tốt nhất cho tiếng Việt (khuyến nghị: qwen2.5:7b)

    # SPOON Agent + MCP
    SPOON_AGENT_ENABLED: bool = True
    SPOON_AGENT_MAX_STEPS: int = 6
    SPOON_AGENT_TIMEOUT: int = 90  # seconds
    SPOON_MCP_TRANSPORT: str = "sse"  # sse | http
    SPOON_MCP_URL: Optional[str] = None
    SPOON_MCP_PATH: str = "/sse"
    
    # LLM - Retry Configuration
    LLM_RETRY_ATTEMPTS: int = 3  # Number of retry attempts
    LLM_RETRY_BASE_DELAY: float = 2.0  # Base delay in seconds
    LLM_RETRY_MAX_DELAY: float = 60.0  # Max delay in seconds
    
    # Database
    DATABASE_URL: str = ""
    
    # JWT
    JWT_SECRET_KEY: str = ""
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_HOURS: int = 24
    
    # File Storage
    FILE_STORAGE_PATH: str = "./storage"
    MAX_FILE_SIZE: int = 52428800  # 50MB
    
    # Application
    DEBUG: bool = True
    SECRET_KEY: str = ""
    
    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:3001"
    
    # MCP Server
    MCP_SERVER_ENABLED: bool = True
    MCP_SERVER_HOST: str = "localhost"
    MCP_SERVER_PORT: int = 8001
    MCP_TRANSPORT: Optional[str] = None
    
    # ChromaDB
    CHROMADB_PATH: str = "./chroma_db"
    
    @field_validator("DEBUG", mode="before")
    @classmethod
    def parse_debug(cls, v):
        """Parse DEBUG from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    @field_validator("MCP_SERVER_ENABLED", mode="before")
    @classmethod
    def parse_mcp_enabled(cls, v):
        """Parse MCP_SERVER_ENABLED from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    @field_validator("OLLAMA_ENABLED", mode="before")
    @classmethod
    def parse_ollama_enabled(cls, v):
        """Parse OLLAMA_ENABLED from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)

    @field_validator("SPOON_AGENT_ENABLED", mode="before")
    @classmethod
    def parse_spoon_agent_enabled(cls, v):
        """Parse SPOON_AGENT_ENABLED from string."""
        if isinstance(v, str):
            return v.lower() in ("true", "1", "yes", "on")
        return bool(v)
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        env_file_encoding = "utf-8"

    @property
    def spoon_mcp_url(self) -> str:
        """Resolve MCP endpoint URL for Spoon agent."""
        if self.SPOON_MCP_URL:
            return self.SPOON_MCP_URL
        transport = (self.SPOON_MCP_TRANSPORT or "sse").lower()
        default_path = self.SPOON_MCP_PATH or ("/mcp" if transport == "http" else "/sse")
        host = self.MCP_SERVER_HOST or "localhost"
        return f"http://{host}:{self.MCP_SERVER_PORT}{default_path}"


settings = Settings()
