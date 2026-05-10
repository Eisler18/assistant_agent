
import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class Config:
  def __init__(self):
    self._timezone = os.getenv('AGENT_TIMEZONE', 'UTC')
    self._llm = None  # Lazy-loaded LLM instance

  @property
  def llm(self):
    if self._llm is None:
      model_name = os.getenv('LLM_MODEL_NAME', 'gemini-2.5-flash-lite')
      api_key = os.getenv('LLM_API_KEY')
      if not api_key:
        raise ValueError('LLM_API_KEY is not set in the environment')

      self._llm = ChatGoogleGenerativeAI(model=model_name, api_key=api_key)

    return self._llm

  @property
  def timezone(self):
    return self._timezone
