"""News summarizer with multi-provider support (OpenAI + Cohere)."""

import asyncio
from news_api import NewsAPI
from llm_providers import LLMProviders


class NewsSummarizer:
    """Summarize news articles using multiple LLM providers."""

    def __init__(self):
        self.news_api = NewsAPI()
        self.llm_providers = LLMProviders()

    def summarize_article(self, article: dict) -> dict:
        """
        Summarize a single article.

        Args:
            article: Article dictionary

        Returns:
            Dictionary with summary and sentiment
        """
        title = article.get("title", "")
        print(f"\nProcessing: {title[:60]}...")

        # Prepare text for summarization (limit content length to control cost)
        article_text = (
            f"Title: {article.get('title','')}\n"
            f"Description: {article.get('description','')}\n"
            f"Content: {(article.get('content','') or '')[:500]}"
        )

        summary_prompt = (
            "Summarize this news article in 2-3 sentences:\n\n"
            f"{article_text}"
        )

        # Step 1: Summarize with OpenAI (primary)
        try:
            print("  → Summarizing with OpenAI...")
            summary = self.llm_providers.ask_openai(summary_prompt)
            print("  ✓ Summary generated (OpenAI)")
            summary_provider = "openai"
        except Exception as e:
            print(f"  ✗ OpenAI summarization failed: {e}")
            print("  → Falling back to Cohere for summary...")
            summary = self.llm_providers.ask_cohere(summary_prompt)
            print("  ✓ Summary generated (Cohere fallback)")
            summary_provider = "cohere"

        # Step 2: Sentiment with Cohere (primary sentiment provider for your lab)
        # If OpenAI summary failed, we already used Cohere for summary—still fine to use Cohere for sentiment.
        try:
            print("  → Analyzing sentiment with Cohere...")
            sentiment_prompt = (
                "Analyze the sentiment of this text.\n\n"
                f"TEXT:\n{summary}\n\n"
                "Return exactly:\n"
                "- Sentiment: positive|negative|neutral\n"
                "- Confidence: 0-100\n"
                "- Tone: a few words\n"
                "- Rationale: 1 short sentence\n"
            )
            sentiment = self.llm_providers.ask_cohere(sentiment_prompt)
            print("  ✓ Sentiment analyzed (Cohere)")
        except Exception as e:
            print(f"  ✗ Cohere sentiment analysis failed: {e}")
            sentiment = "Unable to analyze sentiment"

        return {
            "title": article.get("title", ""),
            "source": article.get("source", ""),
            "url": article.get("url", ""),
            "summary_provider": summary_provider,
            "summary": summary,
            "sentiment": sentiment,
            "published_at": article.get("published_at", ""),
        }

    def process_articles(self, articles: list[dict]) -> list[dict]:
        """
        Process multiple articles.

        Args:
            articles: List of article dictionaries

        Returns:
            List of processed articles
        """
        results = []
        for article in articles:
            try:
                results.append(self.summarize_article(article))
            except Exception as e:
                print(f"✗ Failed to process article: {e}")
                # Continue with next article
        return results

    def generate_report(self, results: list[dict]) -> None:
        """Generate a summary report."""
        print("\n" + "=" * 80)
        print("NEWS SUMMARY REPORT")
        print("=" * 80)

        for i, result in enumerate(results, 1):
            print(f"\n{i}. {result['title']}")
            print(f"   Source: {result['source']} | Published: {result['published_at']}")
            print(f"   URL: {result['url']}")
            print(f"   Summary provider: {result.get('summary_provider','')}")
            print(f"\n   SUMMARY:")
            print(f"   {result['summary']}")
            print(f"\n   SENTIMENT:")
            print(f"   {result['sentiment']}")
            print(f"\n   {'-' * 76}")

        # Cost summary
        summary = self.llm_providers.cost_tracker.get_summary()
        print("\n" + "=" * 80)
        print("COST SUMMARY")
        print("=" * 80)
        print(f"Total requests: {summary['total_requests']}")
        print(f"Total cost: ${summary['total_cost']:.4f}")
        print(f"Total tokens: {summary['total_input_tokens'] + summary['total_output_tokens']:,}")
        print(f"  Input: {summary['total_input_tokens']:,}")
        print(f"  Output: {summary['total_output_tokens']:,}")
        print(f"Average cost per request: ${summary['average_cost']:.6f}")
        print("=" * 80)


# =========================
# Optional (Advanced): Async Processing
# =========================

class AsyncNewsSummarizer(NewsSummarizer):
    """Async version for processing multiple articles concurrently."""

    async def summarize_article_async(self, article):
        """Async version of summarize_article (runs sync work in a thread)."""
        # Note: The LLM API calls themselves are not async in this simple version.
        # This uses threads to allow concurrent processing of multiple articles.
        return await asyncio.to_thread(self.summarize_article, article)

    async def process_articles_async(self, articles, max_concurrent=3):
        """
        Process articles concurrently.

        Args:
            articles: List of articles
            max_concurrent: Maximum concurrent processes

        Returns:
            List of results
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def process_with_semaphore(article):
            async with semaphore:
                return await self.summarize_article_async(article)

        tasks = [process_with_semaphore(article) for article in articles]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter out exceptions
        valid_results = [r for r in results if not isinstance(r, Exception)]
        return valid_results

# Test async version
async def test_async():
    summarizer = AsyncNewsSummarizer()

    # Fetch more articles
    print("Fetching news articles...")
    articles = summarizer.news_api.fetch_top_headlines(category="technology", max_articles=5)

    if articles:
        print(f"\nProcessing {len(articles)} articles concurrently...")
        results = await summarizer.process_articles_async(articles, max_concurrent=3)
        summarizer.generate_report(results)

# Test the module - # asyncio.run(test_async())
if __name__ == "__main__":
    summarizer = NewsSummarizer()

    # Fetch news
    print("Fetching news articles...")
    articles = summarizer.news_api.fetch_top_headlines(category="technology", max_articles=2)

    if not articles:
        print("No articles fetched. Check your News API key.")
    else:
        # Process articles
        print(f"\nProcessing {len(articles)} articles...")
        results = summarizer.process_articles(articles)

        # Generate report
        summarizer.generate_report(results)
