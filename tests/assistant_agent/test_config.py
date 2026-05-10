
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

  def test_config_llm_initialization(self, monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)

    with pytest.raises(ValueError, match='LLM_API_KEY is not set in the environment'):
      config = Config()
      _ = config.llm

    monkeypatch.setenv('LLM_API_KEY', 'fake_api_key')
    config = Config()
    llm_instance = config.llm
    assert llm_instance is not None
    assert config._llm is llm_instance
# pylint: enable=protected-access
