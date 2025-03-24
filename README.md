# News Sentiment Analysis Application

A sophisticated application that analyzes news articles about companies and provides sentiment analysis using AI. The application follows a clean separation between backend (API) and frontend (Streamlit) components.

## Features

- 📰 Real-time news scraping for any company
- 🧠 AI-powered sentiment analysis using Google's Gemini model
- 📊 Detailed analysis including article summaries, sentiment scoring, and topic identification
- 🔍 Comparative analysis across multiple articles, identifying common themes and differences
- 🌐 Support for Hindi translation of sentiment analysis
- 🔊 Text-to-speech capabilities for Hindi translations
- 📱 Clear separation between API backend and Streamlit frontend

## System Architecture

The application follows a clean client-server architecture:

- **Backend API (api.py)**: FastAPI server providing RESTful endpoints for all data processing
  - Handles news scraping, sentiment analysis, and audio generation
  - Provides well-defined endpoints for retrieving data
  - Manages data persistence in the file system
  
- **Frontend UI (app.py)**: Streamlit web application for visualization and user interaction
  - Connects to the API for all data needs
  - Provides a clean, interactive user interface
  - Focuses solely on presentation and user experience
  
- **Utility Services**:
  - `NewsScraper`: Fetches news articles about companies using BeautifulSoup and Requests
  - `GeminiService`: Provides AI-powered analysis using Google's Gemini model
  - `TextToSpeech`: Handles translation and audio generation using gTTS and Googletrans
  
- **Cron Jobs (cron.py)**: Handles scheduled analysis tasks
  - Processes companies in the background
  - Uses asyncio for concurrent processing
  - Updates data files for the frontend to consume

## Technical Implementation Details

### News Scraping Implementation

The `NewsScraper` class uses the following techniques:
- Multi-source scraping from financial news sites
- Dynamic URL generation based on company names and tickers
- HTML parsing using BeautifulSoup4
- Content extraction with text cleaning and normalization
- Date filtering to focus on recent articles
- Rate limiting to avoid overwhelming news sources

### Sentiment Analysis with Gemini AI

The `GeminiService` class leverages Google's Gemini large language model to:
- Generate comprehensive sentiment analysis of news articles
- Extract key topics and themes from articles
- Produce sentiment scores on multiple dimensions (overall, financial impact, reputation)
- Summarize articles with key points
- Identify potential biases in reporting
- Perform cross-article analysis to identify trends

Implementation details:
- Uses structured prompting with detailed instructions
- Includes example outputs to guide the model
- Implements error handling and retry logic
- Manages token usage and context windows
- Processes results into structured JSON format

### Text-to-Speech and Translation

The `TextToSpeech` class provides:
- Translation of English analysis to Hindi using Googletrans
- Generation of audio files from translated text using gTTS
- Caching of audio files to avoid redundant processing
- Format conversion and optimization for web delivery

## Project Setup

### Prerequisites

- Python 3.8 or higher
- Google Gemini API key (Pro or higher tier recommended for best results)
- Sufficient disk space for data storage and audio files

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/news-sentiment-app.git
   cd news-sentiment-app
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a `.env` file in the `utils` directory):
   ```
   GOOGLE_API_KEY=your_gemini_api_key
   ```

4. Create the necessary directory structure:
   ```bash
   mkdir -p data/output/audio
   mkdir -p data/output/analysis
   ```

5. Prepare your company list in `data/company_list.csv` with the following format:
   ```csv
   name,ticker
   Reliance Industries,RELIANCE.NS
   HDFC Bank,HDFCBANK.NS
   Tata Consultancy Services,TCS.NS
   ```

### Configuration Options

The application supports various configuration options that can be modified:

#### API Configuration (api.py)

- `HOST`: The host address for the API server (default: "0.0.0.0")
- `PORT`: The port number for the API server (default: 8000)
- `DATA_DIR`: Directory for storing analysis output (default: "data/output")
- `MAX_WORKERS`: Maximum number of worker threads for background processing

#### Streamlit Configuration (app.py)

- `API_URL`: URL for connecting to the FastAPI service (default: "http://localhost:8000")
- `USE_API`: Whether to use the API or direct file access (default: True)

#### News Scraper Configuration (utils/news_scraper.py)

- `DEFAULT_HEADERS`: User agent and headers for making requests
- `NEWS_SOURCES`: List of news sources to scrape
- `ARTICLE_LIMIT`: Maximum number of articles to retrieve per source

### Running the Application

1. **Start the API server** (must be running for the Streamlit app to function properly):
   ```bash
   cd news-sentiment-app
   python api.py
   ```
   The API will be available at http://localhost:8000

2. **Start the Streamlit app** (in a separate terminal):
   ```bash
   cd news-sentiment-app
   streamlit run app.py
   ```
   The web application will be available at http://localhost:8501

3. **Optional: Run scheduled analysis** for automatic updates:
   ```bash
   python cron.py
   ```

## Model Details

### Gemini Pro Model for Sentiment Analysis and Summarization

This application uses Google's Gemini Pro model (via the `google-generativeai` library) for multiple natural language processing tasks:

1. **Article Summarization**:
   - Gemini Pro converts lengthy news articles into concise, informative summaries
   - Extracts key points while preserving critical information
   - Implementation: Uses structured prompting with a context window of up to 30,000 tokens

2. **Sentiment Analysis**:
   - Performs multi-dimensional sentiment analysis across several aspects:
     - Overall sentiment (positive, neutral, negative)
     - Financial impact assessment (very negative to very positive on a -5 to +5 scale)
     - Reputation impact assessment
     - Market reaction prediction
   - Implementation: Uses specialized prompting that includes examples to guide the model

3. **Cross-Article Analysis**:
   - Identifies common themes, contradictions, and unique insights across multiple articles
   - Generates a comprehensive meta-analysis of the news landscape for a company
   - Implementation: Uses a specialized prompt that combines multiple article summaries as context

### Translation and Text-to-Speech Models

1. **Googletrans (Translation)**:
   - Uses Google Translate's unofficial API to translate English text to Hindi
   - Implementation: Provides natural-sounding translations with specialized handling for financial terminology

2. **Google Text-to-Speech (gTTS)**:
   - Converts Hindi translated text into natural-sounding speech
   - Produces MP3 audio files that can be played in the web interface
   - Implementation: Uses the Hindi language model with slow=False for natural speech cadence

## API Development

The application provides a comprehensive RESTful API built with FastAPI. The API endpoints are documented using OpenAPI and can be accessed through the built-in Swagger UI.

### API Documentation

When the API server is running, full interactive documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Using the API with Postman or Other Tools

1. **Setup**:
   - Import the OpenAPI specification from http://localhost:8000/openapi.json into Postman or similar tools
   - Alternatively, manually create requests to the endpoints documented below

2. **Authentication**:
   - The API currently does not require authentication
   - For production deployment, consider adding API key authentication

3. **Example Postman Collection**:

   A basic Postman collection might include:
   
   - Get Companies:
     - Method: GET
     - URL: http://localhost:8000/companies
   
   - Run Analysis:
     - Method: GET
     - URL: http://localhost:8000/analyze/Reliance Industries
     - Query Parameters:
       - num_articles: 10
   
   - Get Sentiment:
     - Method: GET
     - URL: http://localhost:8000/sentiment/Reliance Industries

### API Endpoints Reference

The FastAPI server provides the following endpoints:

#### Company Management
- `GET /companies` - List all available companies
- `POST /companies` - Add a new company to the tracking list

#### Sentiment Analysis
- `GET /sentiment/{company_name}` - Get sentiment analysis for a specific company
- `GET /audio/{company_name}` - Get Hindi audio summary for a company
- `POST /analyze` - Schedule a background analysis for a company
- `GET /analyze/{company_name}` - Run an immediate analysis for a company

#### Data Management
- `GET /data/{company_name}` - Get raw analysis data for a company
- `DELETE /data/{company_name}` - Remove analysis data for a company
- `GET /health` - Check the health status of the API

### API Usage Examples

```python
import requests

# Get list of companies
response = requests.get("http://localhost:8000/companies")
companies = response.json()["companies"]

# Run analysis for a company
response = requests.get(
    "http://localhost:8000/analyze/Reliance Industries",
    params={"num_articles": 10, "days_back": 30}
)
analysis = response.json()

# Get sentiment analysis results
response = requests.get("http://localhost:8000/sentiment/Reliance Industries")
sentiment = response.json()
```

## Third-Party API Integration

The application integrates several third-party APIs:

### Google Gemini API

- **Purpose**: Provides advanced natural language processing capabilities
- **Integration Details**:
  - Authentication: Uses API key stored in `.env` file
  - Endpoint: Uses the `google-generativeai` Python library
  - Usage Limits: Subject to Google's rate limits and quotas
  - Cost: Free tier available, but production use may require paid subscription
  - Implementation: `GeminiService` class in `utils/gemini_service.py`

### Google Translate API (Unofficial)

- **Purpose**: Translates English analysis to Hindi
- **Integration Details**:
  - Authentication: None required (public API)
  - Library: Uses the `googletrans` Python library (v4.0.0-rc1)
  - Usage Limits: Limited by Google's rate limiting (non-commercial use only)
  - Implementation: `TextToSpeech` class in `utils/text_to_speech.py`

### Google Text-to-Speech API

- **Purpose**: Converts Hindi text to spoken audio
- **Integration Details**:
  - Authentication: None required for client-side generation
  - Library: Uses the `gTTS` Python library
  - Usage Limits: Subject to Google's fair use policy
  - Implementation: `TextToSpeech` class in `utils/text_to_speech.py`

## Assumptions & Limitations

### Assumptions

1. **Internet Connectivity**:
   - The application assumes consistent internet access for news scraping and API calls
   - Temporary disconnections may cause errors in analysis

2. **API Keys and Services**:
   - Assumes valid Google API keys with sufficient quota
   - Assumes third-party services (Google Translate, TTS) remain available and compatible

3. **News Sources**:
   - Assumes specified news sources maintain their current HTML structure
   - Assumes English-language news articles for all companies

4. **Company Information**:
   - Assumes companies listed in company_list.csv are valid entities with news coverage
   - Assumes ticker symbols are accurate for Yahoo Finance

5. **File System**:
   - Assumes write access to the data directory for storing analysis results
   - Assumes sufficient disk space for audio file storage

### Limitations

1. **Scraping Reliability**:
   - News site layout changes may break the scraper
   - Some sites may implement anti-scraping measures
   - Solution: Implement regular monitoring and fallback sources

2. **Translation Quality**:
   - Unofficial Google Translate API may have accuracy issues with financial terminology
   - May struggle with industry-specific jargon
   - Solution: Consider professional translation services for production use

3. **Scalability**:
   - File-based storage limits scalability for large numbers of companies
   - In-memory processing limits the number of concurrent analyses
   - Solution: Implement database storage and distributed processing for production

4. **API Rate Limits**:
   - Google Gemini API has rate limits that may impact analysis speed
   - Translate API has stricter limits as it's unofficial
   - Solution: Implement robust retry logic and rate limiting

5. **Accuracy Considerations**:
   - Sentiment analysis depends on Gemini model's understanding of financial news
   - Results may contain hallucinations or misinterpretations
   - Solution: Implement human review for critical analyses

## Usage Guide

### Web Interface (Streamlit)

1. Select a company from the dropdown in the sidebar
2. Configure analysis options:
   - **Number of Articles**: How many news articles to analyze (5-20 recommended)
   - **Days Back**: How far back in time to look for articles (1-30 days)
   - **Generate Audio**: Whether to create Hindi TTS audio
3. Click "Run Analysis" to fetch and analyze the latest news
4. Explore the results in the three tabs:
   - **Overall Sentiment**: Summary analysis with Hindi translation and audio
   - **News Articles**: Detailed view of each analyzed article
   - **Comparative Analysis**: Cross-article analysis showing common topics and differences

## Project Structure

```
news-sentiment-app/
├── __init__.py             # Package initialization
├── api.py                  # FastAPI backend application
├── app.py                  # Streamlit frontend application
├── cron.py                 # Scheduled background tasks
├── requirements.txt        # Project dependencies
├── README.md               # Project documentation
├── api.log                 # API server logs
├── data/
│   ├── company_list.csv    # List of companies to analyze
│   └── output/             # Output directory for analysis results
│       ├── analysis/       # JSON analysis results
│       └── audio/          # Generated audio files
└── utils/
    ├── __init__.py         # Utility package initialization
    ├── gemini_service.py   # Gemini AI integration
    ├── news_scraper.py     # News scraping functionality
    ├── text_to_speech.py   # Translation and TTS functionality
    └── .env                # Environment variables (not in version control)
```

## Detailed Dependencies Explanation

### Web Scraping and HTTP
- **requests (>=2.31.0)**: Industry-standard HTTP library for making API calls and fetching web pages
- **beautifulsoup4 (>=4.12.0)**: HTML parsing library used to extract content from news websites

### AI and Machine Learning
- **google-generativeai (==0.3.2)**: Official Google client library for accessing the Gemini LLM API
  - Handles authentication, request formatting, and response parsing
  - Supports structured prompting and multiple model versions

### Text-to-Speech and Translation
- **gTTS (==2.5.0)**: Google Text-to-Speech library for generating realistic speech audio
  - Supports multiple languages including Hindi
  - Creates MP3 audio files from text input
- **googletrans (==4.0.0-rc1)**: Unofficial Google Translate API
  - Provides translation between English and Hindi
  - Note: Uses a rate-limited public API not intended for production use at scale

### Web Framework and API
- **fastapi (==0.108.0)**: Modern, high-performance web framework for building APIs
  - Automatic OpenAPI documentation generation
  - Type checking and validation with Pydantic
  - Asynchronous request handling
- **uvicorn (==0.25.0)**: ASGI server for running FastAPI applications
  - High performance with asyncio
  - Production-ready HTTP server
- **streamlit (==1.29.0)**: Interactive data app framework
  - Simplified web UI development
  - Interactive components and data visualization
  - Rapid prototyping capabilities

### Data handling
- **pandas (>=2.1.3)**: Data manipulation and analysis library
  - Used for processing and transforming article data
  - Provides CSV reading/writing capabilities
- **python-dotenv (>=1.0.0)**: Environment variable management
  - Loads environment variables from .env files
  - Keeps sensitive credentials separate from code

### Additional dependencies
- **plotly (>=5.18.0)**: Interactive visualization library
  - Creates sentiment trend charts and comparative visualizations
  - Supports web-based interactive plots
- **pydantic (>=2.0.0)**: Data validation and settings management
  - Validates request and response data structures
  - Provides clear error messages for invalid data
- **starlette (>=0.27.0)**: ASGI framework (used by FastAPI)
  - Handles HTTP connection lifecycle
  - Provides middleware components
- **python-multipart (>=0.0.6)**: Multipart form data parsing
  - Enables file upload capabilities in the API
- **httpx (>=0.24.1)**: Asynchronous HTTP client
  - Used for making non-blocking HTTP requests
  - Supports modern HTTP standards

## Separation of Concerns

This application demonstrates clean separation of concerns:

1. **Backend API (api.py)**:
   - Responsible for data processing and persistence
   - Handles all interactions with external services (Gemini AI, news sources)
   - Provides a consistent API for data access

2. **Frontend UI (app.py)**:
   - Focuses on data visualization and user interaction
   - Consumes the API for all data needs
   - Falls back to local file access only if the API is unavailable

This separation allows for:
- Independent development and testing of each component
- Potential for multiple frontend applications using the same API
- Better maintainability and scalability

## Performance Considerations

- The application is designed for moderate loads and can handle analysis of ~100 companies daily
- For larger deployments, consider:
  - Implementing a proper database instead of file-based storage
  - Setting up a Redis cache for frequent queries
  - Deploying behind a load balancer with multiple API instances
  - Implementing more robust rate limiting for news scraping
  - Using a paid translation API for production use

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 