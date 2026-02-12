"""Unit tests for news summarizer (OpenAI + Cohere)."""

import pytest
from unittest.mock import Mock, patch

from news_api import NewsAPI
from llm_providers import LLMProviders, CostTracker, count_tokens_openai
from summarizer import NewsSummarizer


class TestCostTracker:
    """Test cost tracking functionality."""

    def test_track_request(self):
        tracker = CostTracker()
        cost = tracker.track_request("openai", "gpt-4o-mini", 100, 500)

        assert cost > 0
        assert tracker.total_cost == cost
        assert len(tracker.requests) == 1

    def test_get_summary(self):
        tracker = CostTracker()
        tracker.track_request("openai", "gpt-4o-mini", 100, 200)
        tracker.track_request("cohere", "command-r-plus-08-2024", 150, 300)

        summary = tracker.get_summary()

        assert summary["total_requests"] == 2
        assert summary["total_cost"] > 0
        assert summary["total_input_tokens"] == 250
        assert summary["total_output_tokens"] == 500

    def test_budget_check(self):
        tracker = CostTracker()

        # Should not raise for small amount
        tracker.track_request("openai", "gpt-4o-mini", 100, 100)
        tracker.check_budget(10.00)

        # Should raise for exceeding budget
        tracker.total_cost = 15.00
        with pytest.raises(Exception, match="budget.*exceeded"):
            tracker.check_budget(10.00)


class TestTokenCounting:
    """Test token counting."""

    def test_count_tokens_openai(self):
        text = "Hello, how are you?"
        count = count_tokens_openai(text, model="gpt-4o-mini")

        assert count > 0
        assert count < len(text)  # should be less than character count


class TestNewsAPI:
    """Test News API integration."""

    @patch("news_api.requests.get")
    def test_fetch_top_headlines(self, mock_get):
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "articles": [
                {
                    "title": "Test Article",
                    "description": "Test description",
                    "content": "Test content",
                    "url": "https://example.com",
                    "source": {"name": "Test Source"},
                    "publishedAt": "2026-01-19",
                }
            ],
        }
        mock_get.return_value = mock_response

        api = NewsAPI()
        articles = api.fetch_top_headlines(max_articles=1)

        assert len(articles) == 1
        assert articles[0]["title"] == "Test Article"
        assert articles[0]["source"] == "Test Source"


class TestLLMProviders:
    """Test LLM provider integration (mocked)."""

    @patch("llm_providers.cohere.ClientV2")
    @patch("llm_providers.OpenAI")
    def test_ask_openai(self, mock_openai_class, mock_cohere_class):
        # Mock OpenAI client and response
        mock_openai_client = Mock()
        mock_response = Mock()
        mock_choice = Mock()
        mock_choice.message = Mock(content="Test response")
        mock_response.choices = [mock_choice]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=5)

        mock_openai_client.chat.completions.create.return_value = mock_response
        mock_openai_class.return_value = mock_openai_client

        # Mock Cohere client creation (not used in this test, but needed for __init__)
        mock_cohere_class.return_value = Mock()

        providers = LLMProviders()
        response = providers.ask_openai("Test prompt")

        assert response == "Test response"
        assert mock_openai_client.chat.completions.create.called

    @patch("llm_providers.cohere.ClientV2")
    @patch("llm_providers.OpenAI")
    def test_ask_cohere(self, mock_openai_class, mock_cohere_class):
        # Mock OpenAI client creation (not used in this test, but needed for __init__)
        mock_openai_class.return_value = Mock()

        # Mock Cohere client and response shape: res.message.content[0].text
        mock_cohere_client = Mock()
        mock_res = Mock()
        mock_res.message = Mock(content=[Mock(text="Cohere response")])
        mock_cohere_client.chat.return_value = mock_res

        mock_cohere_class.return_value = mock_cohere_client

        providers = LLMProviders()
        response = providers.ask_cohere("Test prompt")

        assert response == "Cohere response"
        assert mock_cohere_client.chat.called


class TestNewsSummarizer:
    """Test news summarizer core logic."""

    def test_initialization(self):
        summarizer = NewsSummarizer()
        assert summarizer.news_api is not None
        assert summarizer.llm_providers is not None

    @patch.object(LLMProviders, "ask_cohere")
    @patch.object(LLMProviders, "ask_openai")
    def test_summarize_article_success_path(self, mock_openai, mock_cohere):
        # OpenAI summary succeeds; Cohere used for sentiment
        mock_openai.return_value = "Test summary"
        mock_cohere.return_value = "Sentiment: positive"

        summarizer = NewsSummarizer()
        article = {
            "title": "Test Article",
            "description": "Test description",
            "content": "Test content",
            "url": "https://example.com",
            "source": "Test Source",
            "published_at": "2026-01-19",
        }

        result = summarizer.summarize_article(article)

        assert result["title"] == "Test Article"
        assert result["summary"] == "Test summary"
        assert "Sentiment" in result["sentiment"]
        assert result["summary_provider"] == "openai"
        assert mock_openai.called
        assert mock_cohere.called  # sentiment call

    @patch.object(LLMProviders, "ask_cohere")
    @patch.object(LLMProviders, "ask_openai")
    def test_summarize_article_fallback_path(self, mock_openai, mock_cohere):
        # OpenAI summary fails -> Cohere does summary, then Cohere does sentiment
        mock_openai.side_effect = Exception("OpenAI down")
        mock_cohere.side_effect = ["Fallback summary", "Sentiment: neutral"]  # summary, then sentiment

        summarizer = NewsSummarizer()
        article = {
            "title": "Test Article",
            "description": "Test description",
            "content": "Test content",
            "url": "https://example.com",
            "source": "Test Source",
            "published_at": "2026-01-19",
        }

        result = summarizer.summarize_article(article)

        assert result["summary"] == "Fallback summary"
        assert "Sentiment" in result["sentiment"]
        assert result["summary_provider"] == "cohere"
        assert mock_openai.called
        assert mock_cohere.call_count == 2  # summary + sentiment


# Run tests directly (optional)
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
