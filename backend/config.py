from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    demo_mode: bool = True
    database_path: str = "data/supplyrescue.sqlite3"
    asi_one_api_key: str = ""
    asi_model: str = "asi1"
    agentverse_api_key: str = ""
    agent_seed: str = ""
    agent_mailbox: bool = True
    agent_endpoint: str = "http://127.0.0.1:8100/submit"
    admin_api_key: str = ""
    agent_profile_url: str = ""


settings = Settings()
