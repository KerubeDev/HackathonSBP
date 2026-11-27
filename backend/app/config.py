from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://agent:agent@postgres:5432/agent_template"
    openrouter_api_key: str | None = None
    openrouter_model: str = "qwen/qwen-2.5-72b-instruct"
    ollama_base_url: str = "http://host.docker.internal:11434"
    local_model: str = "qwen2.5:7b"
    agent_max_rows: int = 100
    api_key: str | None = None
    log_level: str = 'INFO'
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
settings = Settings()
