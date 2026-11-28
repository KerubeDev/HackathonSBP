from pydantic_settings import BaseSettings, SettingsConfigDict
class Settings(BaseSettings):
    database_url: str = "postgresql+psycopg://agent:agent@postgres:5432/agent_template"
    readonly_database_url: str = "postgresql+psycopg://agent_readonly:agent_readonly@postgres:5432/agent_template"
    openrouter_api_key: str | None = None
    openrouter_model: str = "qwen/qwen-2.5-72b-instruct"
    llm_provider: str = "openrouter"
    ollama_base_url: str = "http://host.docker.internal:11434"
    local_model: str = "qwen2.5:7b"
    qvac_base_url: str = "http://host.docker.internal:8181"
    qvac_model: str = "default"
    allow_deterministic_fallback: bool = False
    execution_mode: str = "sync"
    agent_max_rows: int = 100
    api_key: str | None = None
    log_level: str = 'INFO'
    allowed_chart_types: str = "table,bar,line,area,pie,scatter,radar,heatmap,funnel,gauge,treemap,boxplot,calendar"
    statement_timeout_ms: int = 10000
    max_request_rows: int = 1000
    max_series: int = 20
    max_categories: int = 50
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
settings = Settings()
