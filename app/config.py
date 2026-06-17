from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Asistente Personal WhatsApp"
    whatsapp_token: str = ""
    whatsapp_phone_number_id: str = ""
    whatsapp_verify_token: str = ""
    personal_whatsapp_to: str = ""
    enable_scheduler: bool = False
    morning_report_time: str = "08:00"
    linkedin_ideas_time: str = "12:00"
    timezone: str = "America/Santiago"
    task_secret: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
