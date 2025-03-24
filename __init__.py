"""
News Sentiment Analysis Application

This package provides tools for news article scraping, sentiment analysis,
and translation/text-to-speech capabilities for financial news.
"""

# Version information
__version__ = "1.0.0"

# Import key components for easy access
from utils.news_scraper import NewsScraper
from utils.gemini_service import GeminiService
from utils.text_to_speech import TextToSpeech

# Make certain modules available when importing the package
__all__ = [
    'NewsScraper',
    'GeminiService',
    'TextToSpeech',
] 