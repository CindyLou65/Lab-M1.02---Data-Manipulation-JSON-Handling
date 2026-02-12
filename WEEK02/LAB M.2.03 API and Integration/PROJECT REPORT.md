Lab M2.03 API and Integraion Patterns Lab- Multi-Provider News Summarizer
Cindy Lund

PROJECT REPORT / REEFLECTIONS

# Project Reflection

1. Challenges I Faced
One of the main challenges was integrating multiple LLM providers into a clean, modular architecture while maintaining separation of concerns. Initially, the assignment referenced Anthropic, and I did this as I thought the Cohere would work with Antropic. It did not, so then I used Cohere instead. This required carefully adapting configuration management, provider abstraction, cost tracking, and unit tests without breaking the system structure.

Another challenge was implementing reliable cost tracking across providers. Each API exposes token usage differently, and some SDK versions do not consistently return usage metadata. It was harder to find token information on Cohere. Ensuring accurate and robust cost estimation required additional logic.

Finally, adding asynchronous processing while using synchronous SDKs required careful design to avoid rewriting the entire provider layer.

2. How I Solved Them
To handle provider flexibility, I abstracted each provider inside a unified LLMProviders class and implemented fallback logic between them.

For cost tracking, I created a dedicated CostTracker class and implemented flexible token extraction with fallback estimation when usage data was unavailable.

To support concurrency without breaking compatibility, I used asyncio.to_thread() and semaphores, enabling concurrent processing while preserving rate limits and budget control.

3. What I Learned
This project strengthened my understanding of production-style API integration, multi-provider LLM architectures, fallback mechanisms, and cost monitoring. I also gained practical experience in writing unit tests with mocks and managing secure configuration using environment variables.

4. Ideas for Improvement
Future improvements could include true asynchronous HTTP requests, persistent logging of cost metrics, response caching to reduce API calls, and a web-based dashboard for monitoring system performance in real time.