from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # GitHub Models (default LLM provider)
    github_token: str = ""
    llm_default_max_tokens: int = 2048

    # Per-task LLM overrides
    generation_llm_model: str = "gpt-4o-mini"
    generation_llm_temperature: float = 0.7
    generation_llm_max_tokens: int = 2048

    evaluation_llm_model: str = "gpt-4o-mini"
    evaluation_llm_temperature: float = 0.0
    evaluation_llm_max_tokens: int = 2048

    synthesis_llm_model: str = "gpt-4o-mini"
    synthesis_llm_temperature: float = 0.2
    synthesis_llm_max_tokens: int = 8192

    # Research pipeline
    max_depth: int = 3
    max_children: int = 2
    keep_top_k: int = 5
    execution_workers: int = 4
    evaluation_workers: int = 2

    # Repo clone cache
    codeatlas_cache_dir: str = ""


settings = Settings()
