
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
import pytest

from assistant_agent.config import Config

# pylint: disable=protected-access
class TestConfig:
  def test_config_initialization(self, monkeypatch):
    monkeypatch.setenv('AGENT_TIMEZONE', 'UTC')

    config = Config()
    assert config is not None
    assert config._llm is None
    assert config.timezone == 'UTC'

  def test_config_google_llm_initialization(self, monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    monkeypatch.setenv('LLM_MODEL_NAME', 'gemini-2.5-flash-lite')

    with pytest.raises(ValueError, match='LLM_API_KEY is not set in the environment'):
      config = Config()
      _ = config.llm

    monkeypatch.setenv('LLM_API_KEY', 'fake_api_key')
    config = Config()
    llm_instance = config.llm
    assert llm_instance is not None
    assert isinstance(config._llm, ChatGoogleGenerativeAI)

  def test_config_openai_llm_initialization(self, monkeypatch):
    monkeypatch.setenv('LLM_API_KEY', 'fake_api_key')
    monkeypatch.setenv('LLM_MODEL_NAME', 'gpt-3.5-turbo')
    monkeypatch.setenv('LLM_API_URL', 'https://api.openai.com/v1')
    config = Config()
    llm_instance = config.llm
    assert llm_instance is not None
    assert isinstance(config._llm, ChatOpenAI)
# pylint: enable=protected-access
