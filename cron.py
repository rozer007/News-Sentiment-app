import pandas as pd
import os
import pickle
import json
import asyncio
import logging
from datetime import datetime
from utils.news_scraper import NewsScraper
from utils.gemini_service import GeminiService
from utils.text_to_speech import TextToSpeech

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("cron.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("cron")

async def process_company(
    company_name: str, 
    news_scraper: NewsScraper, 
    gemini_service: GeminiService,
    tts_service: TextToSpeech,
    output_dir: str,
    num_articles: int = 10,
    days_back: int = 30,
    generate_tts: bool = True
) -> bool:
    """
    Process a single company asynchronously
    
    Args:
        company_name: Name of the company to analyze
        news_scraper: Initialized NewsScraper instance
        gemini_service: Initialized GeminiService instance
        tts_service: Initialized TextToSpeech instance
        output_dir: Directory to save output files
        num_articles: Number of articles to analyze
        days_back: Number of days back to look for news
        generate_tts: Whether to generate TTS
        
    Returns:
        True if successful, False otherwise
    """
    try:
        logger.info(f"Processing company: {company_name}")
        
        # Get news articles
        articles = news_scraper.get_company_news(
            company_name=company_name,
            num_articles=num_articles,
        )
        
        if not articles:
            logger.warning(f"No articles found for {company_name}, skipping...")
            return False
        
        # Analyze articles with Gemini
        analysis_result = gemini_service.analyze_articles(company_name, articles)
        
        # Add timestamp
        analysis_result["Timestamp"] = datetime.now().isoformat()
        
        # Generate TTS if requested
        if generate_tts:
            try:
                analysis_result = await tts_service.process_sentiment_tts(analysis_result,company_name)
                logger.info(f"Generated TTS for {company_name}")
            except Exception as e:
                logger.error(f"Error generating TTS for {company_name}: {e}")
                # Continue with saving the analysis even if TTS fails
        
        # Save results as pickle
        output_file = os.path.join(output_dir, f"{company_name.lower().replace(' ', '_')}.pkl")
        with open(output_file, 'wb') as f:
            pickle.dump(analysis_result, f)
        
        # Save as JSON for easier inspection
        json_path = os.path.join(output_dir, f"{company_name.lower().replace(' ', '_')}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(analysis_result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Successfully processed {company_name} and saved results")
        return True
        
    except Exception as e:
        logger.error(f"Error processing {company_name}: {e}", exc_info=True)
        return False

async def main():
    """
    Main cron job function to scrape news and analyze sentiment for all companies
    """
    logger.info(f"Starting cron job at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize services
    news_scraper = NewsScraper()
    gemini_service = GeminiService()
    tts_service = TextToSpeech()
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join('data', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    # Read company list
    try:
        companies_df = pd.read_csv(os.path.join('data', 'company_list.csv'))
        logger.info(f"Found {len(companies_df)} companies in the list")
    except Exception as e:
        logger.error(f"Error reading company list: {e}")
        return
    
    # Create a semaphore to limit concurrent processing
    # This prevents overwhelming the API services
    semaphore = asyncio.Semaphore(3)  # Process up to 3 companies concurrently
    
    async def process_with_semaphore(company_name):
        async with semaphore:
            return await process_company(
                company_name, 
                news_scraper, 
                gemini_service,
                tts_service,
                output_dir
            )
    
    # Create tasks for all companies
    tasks = [process_with_semaphore(row['name']) for _, row in companies_df.iterrows()]
    
    # Process all companies concurrently (but limited by the semaphore)
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Count successful and failed processes
    success_count = sum(1 for r in results if r is True)
    error_count = sum(1 for r in results if r is False or isinstance(r, Exception))
    
    logger.info(f"Cron job completed: {success_count} companies processed successfully, {error_count} failed")
    logger.info(f"Cron job completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Run the main function
    asyncio.run(main()) 