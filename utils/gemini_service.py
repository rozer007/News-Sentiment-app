import google.generativeai as genai
import os
import json
from typing import List, Dict, Any
from dotenv import load_dotenv
import time
# Load environment variables
load_dotenv()

class GeminiService:
    """
    Class for interacting with Google's Gemini AI model for text analysis
    """
    
    def __init__(self, api_key: str = None):
        """
        Initialize the Gemini service
        
        Args:
            api_key: Google API key (defaults to environment variable)
        """
        # Use provided API key or get from environment variables
        api_key = api_key or os.getenv("GOOGLE_API_KEY")
        
        if not api_key:
            raise ValueError("Google API key is required. Set GOOGLE_API_KEY environment variable or pass it to the constructor.")
        
        # Configure the Gemini API
        genai.configure(api_key=api_key)
        
        # Get the model
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def analyze_articles(self, company_name: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze news articles using Gemini AI
        
        Args:
            company_name: Name of the company
            articles: List of article dictionaries with title and content
            
        Returns:
            Dictionary with analysis results
        """
        if not articles:
            return {
                "Company": company_name,
                "Articles": [],
                "Comparative Sentiment Score": {},
                "Final Sentiment Analysis": "No articles available for analysis."
            }
        
        # Process each article individually
        processed_articles = []
        
        for article in articles:
            article_analysis = self._analyze_single_article(article)
            processed_articles.append(article_analysis)
            time.sleep(20)


        
        # Generate comparative analysis
        if len(processed_articles) > 1:
            comparative_analysis = self._generate_comparative_analysis(processed_articles)
        else:
            comparative_analysis = {
                "Sentiment Distribution": {},
                "Coverage Differences": [],
                "Topic Overlap": {}
            }
        
        # Generate final sentiment analysis
        final_sentiment = self._generate_final_sentiment(company_name, processed_articles)
        
        # Compile the complete analysis
        result = {
            "Company": company_name,
            "Articles": processed_articles,
            "Comparative Sentiment Score": comparative_analysis,
            "Final Sentiment Analysis": final_sentiment
        }
        
        return result
    
    def _analyze_single_article(self, article: Dict[str, str]) -> Dict[str, Any]:
        """
        Analyze a single article using Gemini AI
        
        Args:
            article: Dictionary containing article title and content
            
        Returns:
            Dictionary with analysis results for the article
        """
        try:
            prompt = f"""
            Analyze the following news article:
            
            Title: {article['title']}
            Content: {article['content']}
            
            Please provide:
            1. A concise summary of the article (2-3 sentences)
            2. The sentiment of the article (Positive, Negative, or Neutral)
            3. A list of main topics covered in the article
            
            Format your response as a JSON with the following structure:
            {{
                "Summary": "...",
                "Sentiment": "...",
                "Topics": ["topic1", "topic2", ...]
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            response_text = response.text
            # Extract the JSON part
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                analysis = json.loads(json_str)
            else:
                # If JSON parsing fails, create a basic structure
                analysis = {
                    "Summary": "Failed to generate summary.",
                    "Sentiment": "Neutral",
                    "Topics": ["Unknown"]
                }
            
            # Combine with original article info
            result = {
                "Title": article['title'],
                "URL": article.get('url', ''),
                "Summary": analysis.get("Summary", "No summary available"),
                "Sentiment": analysis.get("Sentiment", "Neutral"),
                "Topics": analysis.get("Topics", ["Unknown"])
            }
            
            return result
            
        except Exception as e:
            print(f"Error analyzing article: {e}")
            return {
                "Title": article['title'],
                "URL": article.get('url', ''),
                "Summary": "Error analyzing article content.",
                "Sentiment": "Neutral",
                "Topics": ["Error"]
            }
    
    def _generate_comparative_analysis(self, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate comparative analysis across multiple articles
        
        Args:
            articles: List of processed article dictionaries
            
        Returns:
            Dictionary with comparative analysis
        """
        try:
            # Count sentiments
            sentiments = [article["Sentiment"] for article in articles]
            sentiment_distribution = {
                "Positive": sentiments.count("Positive"),
                "Negative": sentiments.count("Negative"),
                "Neutral": sentiments.count("Neutral")
            }
            
            # Prepare article summaries for Gemini
            article_summaries = []
            for i, article in enumerate(articles):
                article_summaries.append(f"Article {i+1}: {article['Title']}\nSummary: {article['Summary']}\nSentiment: {article['Sentiment']}\nTopics: {', '.join(article['Topics'])}")
            
            all_summaries = "\n\n".join(article_summaries)
            
            # Generate comparative analysis with Gemini
            prompt = f"""
            Analyze the following news articles and provide a comparative analysis:
            
            {all_summaries}
            
            Please provide:
            1. Key coverage differences between the articles and their potential impact
            2. Analysis of topic overlap (common topics and unique topics per article)
            
            Format your response as a JSON with the following structure:
            {{
                "Coverage Differences": [
                    {{
                        "Comparison": "...",
                        "Impact": "..."
                    }},
                    ...
                ],
                "Topic Overlap": {{
                    "Common Topics": ["topic1", "topic2", ...],
                    "Unique Topics in Article 1": ["topic1", "topic2", ...],
                    "Unique Topics in Article 2": ["topic1", "topic2", ...],
                    ...
                }}
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # Parse the JSON response
            response_text = response.text
            
            # Extract the JSON part
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                comparative = json.loads(json_str)
            else:
                # If JSON parsing fails, create a basic structure
                comparative = {
                    "Coverage Differences": [
                        {
                            "Comparison": "Failed to analyze coverage differences.",
                            "Impact": "Unknown"
                        }
                    ],
                    "Topic Overlap": {
                        "Common Topics": [],
                        "Unique Topics per Article": {}
                    }
                }
            
            # Add sentiment distribution to the result
            result = {
                "Sentiment Distribution": sentiment_distribution,
                "Coverage Differences": comparative.get("Coverage Differences", []),
                "Topic Overlap": comparative.get("Topic Overlap", {})
            }
            
            return result
            
        except Exception as e:
            print(f"Error generating comparative analysis: {e}")
            return {
                "Sentiment Distribution": {},
                "Coverage Differences": [
                    {
                        "Comparison": f"Error generating comparative analysis: {str(e)}",
                        "Impact": "Unknown"
                    }
                ],
                "Topic Overlap": {}
            }
    
    def _generate_final_sentiment(self, company_name: str, articles: List[Dict[str, Any]]) -> str:
        """
        Generate final sentiment analysis summary
        
        Args:
            company_name: Name of the company
            articles: List of processed article dictionaries
            
        Returns:
            String with final sentiment analysis
        """
        try:
            # Prepare article summaries for Gemini
            article_summaries = []
            for i, article in enumerate(articles):
                article_summaries.append(f"Article {i+1}: {article['Title']}\nSummary: {article['Summary']}\nSentiment: {article['Sentiment']}")
            
            all_summaries = "\n\n".join(article_summaries)
            
            prompt = f"""
            Based on the following news articles about {company_name}:
            
            {all_summaries}
            
            Provide a concise final sentiment analysis in 2-3 sentences. Include:
            1. The overall sentiment toward {company_name} (positive, negative, or mixed)
            2. Key factors driving this sentiment
            3. Brief implications for the company
            
            Respond with only the final sentiment analysis in 2-3 sentences.
            """
            
            response = self.model.generate_content(prompt)
            final_sentiment = response.text.strip()
            
            return final_sentiment
            
        except Exception as e:
            print(f"Error generating final sentiment: {e}")
            return f"Unable to generate final sentiment analysis for {company_name} due to an error." 