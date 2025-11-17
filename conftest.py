import os
import pytest
from dotenv import load_dotenv

@pytest.fixture(scope='session', autouse=True)
def load_env():
    """
    Fixture para cargar automáticamente el archivo .env antes de que se ejecuten las pruebas,
    especificando una ruta explícita.
    """
    dotenv_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(dotenv_path):
        load_dotenv(dotenv_path=dotenv_path)