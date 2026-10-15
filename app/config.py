import os
from pydantic import BaseModel


class Settings(BaseModel):
    PROJECT_NAME: str = "Inventory Order API"
    VERSION: str = "1.0.0"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./inventory.db")


settings = Settings()
