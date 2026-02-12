# 📰 Multi-Provider News Summarizer
Cindy Lund

A production-style news processing system that:

- Fetches live news articles from an external API
- Uses OpenAI (gpt-4o-mini) for article summarization
- Uses Cohere (Command R+) for sentiment analysis
- Implements fallback logic between providers
- Tracks API token usage and estimated costs
- Supports optional asynchronous concurrent processing
- Includes unit tests for core components

The goal is to simulate a production-ready system capable of processing hundreds of articles per day while controlling API costs and maintaining reliability.

---

## ⚙️ Setup Instructions

### 1️⃣ Clone Repository
2️⃣ Install dependencies

3️⃣ Configure environment variables
Create a .env file using .env.example as a template:

▶️ How to Run
Run the main application:
python main.py
You will be prompted to choose:
*News category
*Number of articles
*Whether to use async processing
Run Unit Tests:  pytest -v
All tests should pass successfully.
Run Unit Tests:  pytest -v
All tests should pass successfully.

📊 Example Output
Processing 3 articles concurrently...

SUMMARY:
The article discusses...

SENTIMENT:
- Sentiment: positive
- Confidence: 92
- Tone: enthusiastic
- Rationale: ...

================================================================================
COST SUMMARY
================================================================================
Total requests: 6
Total cost: $0.0019
Total tokens: 1,024
Average cost per request: $0.000316

💰 Cost Analysis

The application tracks:
*Input tokens
*Output tokens
*Total requests
*Estimated cost per model
*Average cost per request

Cost control features include:
*Daily budget enforcement
*Warning at 90% budget usage
*Rate limiting per provider
*Truncation of article content before LLM calls
*This simulates a production environment where API costs must be monitored and controlled.

🧪 Test Coverage
The project includes unit tests for:
*Cost tracking
*Token counting
*News API integration (mocked)
*OpenAI integration (mocked)
*Cohere integration (mocked)
*Fallback logic
*Summarizer functionality

All tests pass using:  pytest -v

🚀 Optional Advanced Feature
An async version of the summarizer allows concurrent article processing using asyncio and semaphores while maintaining rate limits.

✅ Features Implemented
*External API integration with error handling
*Multi-provider LLM architecture
*Fallback logic between providers
*Token-based cost tracking
*Budget monitoring
*Rate limiting
*Unit testing with mocks
*Environment-based configuration
*Optional concurrent processing




FOR MY Personal Information: 
Information on the Requirments File
# openai: openai>=1.12.0 >=1.12.0: This means you need at least version 1.12.0. If a newer version is available, it can also be used.

# This package is used to interact with Anthropic's AI models. >=0.18.0: Requires version 0.18.0 or higher.

#requests: A very popular package for making HTTP requests, which is often used to communicate with web services.
#>=2.31.0: You need version 2.31.0 or newer.
# HTTP client library  Used for:  Fetching news articles from external APIs

#python-dotenv: This package helps you manage environment variables. It's commonly used to store sensitive information like API keys securely.
#>=1.0.0: Requires version 1.0.0 or above.

#aiohttp: A package for handling HTTP requests asynchronously. This can make your code run faster by doing multiple things at once.
#>=3.9.0: You need at least version 3.9.0.

#tiktoken: This package is used for tokenizing text, which is a crucial part of processing language in AI models.
#>=0.5.0: Requires version 0.5.0 or higher.

#tiktoken: This package is used for tokenizing text, which is a crucial part of processing language in AI models.
#>=0.5.0: Requires version 0.5.0 or higher. For counting tokens in text, which is important for managing input sizes when working with AI models.   

#pytest: A testing framework for Python. It allows you to write simple and scalable test cases for your code.
#>=7.4.0: You need version 7.4.0 or newer. Used for: Writing and running tests to ensure your code works correctly.
# used for writing unit tests, validating API logi, Ensuring fallback logid works

# How to Use requirements.txt
#To install these dependencies, you typically use a tool called pip, which is Python's package installer. You would run the following command in your terminal:
#pip install -r requirements.txt
#This command tells pip to read the requirements.txt file and install all the packages listed, ensuring they're at least the minimum versions specified