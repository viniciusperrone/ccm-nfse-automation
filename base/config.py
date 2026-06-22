import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    _CCM = {
        "BELO_HORIZONTE": os.getenv("CCM_BELO_HORIZONTE"),
        "RIO_DE_JANEIRO": os.getenv("CCM_RIO_DE_JANEIRO"),
        "BARUERI": os.getenv("CCM_BARUERI"),
        "PORTO_ALEGRE": os.getenv("CCM_PORTO_ALEGRE"),
        "NOVA_LIMA": os.getenv("CCM_NOVA_LIMA"),
    }
    CAPTCHA_API_KEY = os.getenv("CAPTCHA_API_KEY")

    @classmethod
    def get_ccm(cls, city: str):
        value = cls._CCM.get(city.upper())
        return value or None
