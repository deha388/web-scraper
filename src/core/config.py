from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Boat Price Tracker"
    MONGO_URI: str = "mongodb://localhost:27017"
    MONGO_DB: str = "boat_tracker"
    
    class Config:
        env_file = ".env"

settings = Settings() 