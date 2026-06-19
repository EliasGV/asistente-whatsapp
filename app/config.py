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
    vehicle_one_year: int = 2010
    vehicle_one_digit: str = "2"
    vehicle_two_year: int = 2019
    vehicle_two_digit: str = "8"
    linkedin_client_id: str = ""
    linkedin_client_secret: str = ""
    linkedin_redirect_uri: str = ""
    linkedin_state_secret: str = "linkedin-2450"
    linkedin_access_token: str = ""
    linkedin_person_urn: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
