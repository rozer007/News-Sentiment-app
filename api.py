from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import pickle
import json
import logging
import pandas as pd
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn

from utils.text_to_speech import TextToSpeech
from utils.news_scraper import NewsScraper
from utils.gemini_service import GeminiService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("api.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("api")

# Initialize the FastAPI app
app = FastAPI(
    title="News Sentiment Analysis API",
    description="""API for extracting and analyzing news articles about companies.

This API provides endpoints for accessing sentiment analysis data and running new analyses.""",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
tts_service = TextToSpeech()


# Define Pydantic models for request/response validation
class CompanyInfo(BaseModel):
    name: str
    ticker: Optional[str] = None


class ArticleInfo(BaseModel):
    Title: str
    Content: Optional[str] = None
    Summary: Optional[str] = None
    Sentiment: str
    Sentiment_Score: float = 0.0
    URL: Optional[str] = None
    Topics: Optional[List[str]] = None


class SentimentAnalysis(BaseModel):
    Company: str
    Articles: List[ArticleInfo]
    Overall_Sentiment: str
    Sentiment_Score: float
    Comparative_Analysis: Optional[str] = None
    Comparative_Sentiment_Score: Optional[float] = None
    Hindi_Translation: Optional[str] = None
    Audio_Path: Optional[str] = None
    Timestamp: Optional[str] = None
    Ticker: Optional[str] = None


# Helper functions
def load_company_list():
    """Load the list of companies from the CSV file"""
    try:
        csv_path = os.path.join('data', 'company_list.csv')
        if os.path.exists(csv_path):
            return pd.read_csv(csv_path)
        else:
            logger.error(f"Company list file not found at {csv_path}")
            return pd.DataFrame(columns=['name', 'ticker'])
    except Exception as e:
        logger.error(f"Error loading company list: {e}")
        return pd.DataFrame(columns=['name', 'ticker'])


def get_pickle_path(company_name: str) -> str:
    """Get the path to the pickle file for a company"""
    filename = f"{company_name.lower().replace(' ', '_')}.pkl"
    return os.path.join('data', 'output', filename)


def load_sentiment_data(company_name: str) -> Optional[Dict[str, Any]]:
    """Load sentiment data for a specific company from pickle file"""
    try:
        pickle_path = get_pickle_path(company_name)
        if not os.path.exists(pickle_path):
            return None

        with open(pickle_path, 'rb') as f:
            data = pickle.load(f)

        return data
    except Exception as e:
        logger.error(f"Error loading sentiment data for {company_name}: {e}")
        return None

async def generate_hindi_tts(sentiment_data: Dict[str, Any],company_name: str) -> Dict[str, Any]:
    """Generate Hindi TTS for a company's sentiment analysis"""
    # print(("Hindi_Translation" not in sentiment_data or "Audio_Path" not in sentiment_data))
    # if "Hindi_Translation" not in sentiment_data or "Audio_Path" not in sentiment_data:
    try:
        hindi_text= await tts_service.process_sentiment_tts(sentiment_data,company_name)
        return hindi_text
    except Exception as e:
        logger.error(f"Error generating Hindi TTS: {e}")

    return sentiment_data


async def analyze_company(company_name: str) -> Dict[str, Any]:
    """Analyze news articles for a company and generate sentiment analysis"""
    logger.info(f"Analysis for company: {company_name}")

    try:
        # Initialize services
        news_scraper = NewsScraper()
        gemini_service = GeminiService()

        # Scrape news articles - standard 10 articles
        articles = news_scraper.get_company_news(
            company_name=company_name,
            num_articles=10,
        )

        if not articles:
            logger.warning(f"No articles found for {company_name}")
            return {
                "Company": company_name,
                "Articles": [],
                "Overall_Sentiment": "Unknown",
                "Sentiment_Score": 0,
                "Final_Sentiment_Analysis": "No articles found for analysis."
            }

        # Analyze with Gemini
        logger.info(f"Analyzing {len(articles)} articles with Gemini")
        analysis = gemini_service.analyze_articles(company_name, articles)

        # Add ticker if available
        companies_df = load_company_list()
        company_row = companies_df[companies_df['name'] == company_name]
        if not company_row.empty and 'ticker' in company_row.columns:
            analysis["Ticker"] = company_row.iloc[0]['ticker']

        # Generate Hindi TTS
        analysis = await tts_service.process_sentiment_tts(analysis,company_name)

        # Save results
        output_dir = os.path.join('data', 'output')
        os.makedirs(output_dir, exist_ok=True)

        # Save as pickle
        pickle_path = get_pickle_path(company_name)
        with open(pickle_path, 'wb') as f:
            pickle.dump(analysis, f)

        # Save as JSON for easier inspection
        json_path = os.path.join(output_dir, f"{company_name.lower().replace(' ', '_')}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)

        logger.info(f"Analysis completed and saved for {company_name}")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing {company_name}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error analyzing {company_name}: {str(e)}")


# API Endpoints
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "News Sentiment Analysis API",
        "version": "1.0.0",
        "description": "API for extracting and analyzing news articles about companies"
    }


@app.get("/companies")
async def get_companies():
    """Get the list of available companies"""
    companies_df = load_company_list()
    return {"companies": companies_df.to_dict(orient="records")}


@app.get("/sentiment/{company_name}")
async def get_sentiment(
        company_name: str,
        generate_tts: bool = True):

    """
    Get sentiment analysis for a specific company

    Args:
        company_name: Name of the company
        generate_tts: Whether to generate TTS if not already present
    """
    # Check if the company exists
    companies_df = load_company_list()
    if company_name not in companies_df['name'].values:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

    # Load existing sentiment data
    sentiment_data = load_sentiment_data(company_name)
    if not sentiment_data:
        raise HTTPException(status_code=404, detail=f"No sentiment data found for {company_name}")


    # Generate Hindi TTS if requested
    if generate_tts or ("Hindi_Translation" not in sentiment_data or "Audio_Path" not in sentiment_data):
        try:
            sentiment_data = await generate_hindi_tts(sentiment_data,company_name)
            # Save updated data with TTS
            print("Audio path",sentiment_data['Audio_Path'])
            pickle_path = get_pickle_path(company_name)
            with open(pickle_path, 'wb') as f:
                pickle.dump(sentiment_data, f)

        except Exception as e:
            logger.error(f"Error generating TTS for {company_name}: {e}")

    return sentiment_data


@app.get("/audio/{company_name}")
async def get_audio(company_name: str):
    """
    Get the audio file for a company's sentiment analysis

    Args:
        company_name: Name of the company
    """
    # Check if the company exists
    companies_df = load_company_list()
    if company_name not in companies_df['name'].values:
        raise HTTPException(status_code=404, detail=f"Company '{company_name}' not found")

    # Load sentiment data
    sentiment_data = load_sentiment_data(company_name)
    if not sentiment_data:
        raise HTTPException(status_code=404, detail=f"No sentiment data found for {company_name}")

    # Generate TTS if not already present
    if "Audio_Path" not in sentiment_data or not os.path.exists(sentiment_data["Audio_Path"]):
        try:
            sentiment_data = await generate_hindi_tts(sentiment_data,company_name)

            # Save updated data
            pickle_path = get_pickle_path(company_name)
            with open(pickle_path, 'wb') as f:
                pickle.dump(sentiment_data,f)
        except Exception as e:
            logger.error(f"Error generating hindi audio for {company_name}: {e}")

    # Return the audio file
    audio_path = sentiment_data.get("Audio_Path")
    if not audio_path or not os.path.exists(audio_path):
        raise HTTPException(status_code=404, detail="Audio file not found")

    return FileResponse(
        audio_path,
        media_type="audio/mpeg",
        filename=f"{company_name.lower().replace(' ', '_')}_sentiment.mp3"
    )


if __name__ == "__main__":
    # Ensure the output directory exists
    os.makedirs(os.path.join('data', 'output'), exist_ok=True)

    # Run the API server
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True) 