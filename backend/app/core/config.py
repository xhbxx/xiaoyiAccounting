from pydantic_settings import BaseSettings,SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    APP_ENV:str="dev"

    DB_HOST:str
    DB_PORT:int=3306
    DB_USER:str
    DB_PASSWORD:str
    DB_NAME:str

    JWT_SECRET_KEY:str
    JWT_ALGORITHM:str="HS256"
    JWT_EXPIRE_MINUTES:int=10080

    WECHAT_APPID:str
    WECHAT_SECRET:str

    SERVER_HOST:str="127.0.0.1"
    SERVER_PORT:int=8000

settings=Settings()


