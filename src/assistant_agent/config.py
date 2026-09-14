
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI

load_dotenv()

_DATABASE_URL_VAR_BY_ENVIRONMENT = {
  'production': 'DATABASE_URL',
  'development': 'DEV_DATABASE_URL',
  'test': 'TEST_DATABASE_URL',
}

class Config:
  def __init__(self):
    self._timezone = os.getenv('AGENT_TIMEZONE', 'UTC')
    self._briefing_enabled = os.getenv('BRIEFING_ENABLED', 'true').lower() == 'true'
    self._environment = os.getenv('ENVIRONMENT', 'development')
    self._database_url = os.getenv(
      _DATABASE_URL_VAR_BY_ENVIRONMENT.get(self._environment, 'DEV_DATABASE_URL')
    )
    self._llm = None  # Lazy-loaded LLM instance

  @property
  def llm(self):
    if self._llm is None:
      model_name = os.getenv('LLM_MODEL_NAME', 'gemini-2.5-flash-lite')
      api_key = os.getenv('LLM_API_KEY')
      url = os.getenv('LLM_API_URL')
      if not api_key:
        raise ValueError('LLM_API_KEY is not set in the environment')

      if 'gemini' in model_name.lower():
        self._llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)
      else:
        self._llm = ChatOpenAI(
          model=model_name,
          api_key=api_key,
          base_url=url
        )

    return self._llm

  @property
  def timezone(self):
    return self._timezone

  @property
  def briefing_enabled(self):
    return self._briefing_enabled

  @property
  def environment(self):
    return self._environment

  @property
  def database_url(self):
    return self._database_url
