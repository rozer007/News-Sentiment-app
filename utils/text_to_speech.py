from gtts import gTTS
from googletrans import Translator
import os
from typing import Dict, Any

class TextToSpeech:
    """
    Class for translating text to Hindi and generating TTS output
    """
    
    def __init__(self):
        """Initialize the translator"""
        self.translator = Translator()
    
    async def translate_to_hindi(self, text: str) -> str:
        """
        Translate English text to Hindi
        
        Args:
            text: English text to translate
            
        Returns:
            Translated Hindi text
        """
        try:
            # For googletrans 4.0.0-rc1, translate() returns a coroutine
            translation = await self.translator.translate(text, dest='hi')
            return translation.text
        except Exception as e:
            print(f"Translation error: {e}")
            return text  # Return original text if translation fails
    
    def generate_audio(self, hindi_text: str, company_name:str,lang: str = 'hi',) -> str:
        """
        Generate audio file from text
        
        Args:
            hindi_text: Text to convert to speech
            lang: Language code (default: Hindi)
            company_name : to save the audio file
            
        Returns:
            Path to the generated audio file
        """
        try:

            audio_dir = os.path.join('data', 'audio')
            os.makedirs(audio_dir, exist_ok=True)

            audio_filename = f"{company_name}_hindi.mp3"
            audio_path = os.path.join(audio_dir, audio_filename)
            print(audio_path)

            if hindi_text and hindi_text.strip():
                tts = gTTS(text=hindi_text, lang=lang, slow=False)
                tts.save(audio_path)
            else:
                audio_path = None

            return audio_path
        except Exception as e:
            print(f"TTS generation error: {e}")
            return "None"
    
    async def process_sentiment_tts(self, sentiment_data: Dict[str, Any],company_name: str) -> Dict[str, Any]:
        """
        Process sentiment data to generate Hindi TTS
        
        Args:
            sentiment_data: Dictionary containing sentiment analysis results
            company_name : to pass to generate audio function
            
        Returns:
            Dictionary with added TTS file path
        """
        # Extract the final sentiment analysis
        final_sentiment = sentiment_data.get("Final Sentiment Analysis", "No sentiment analysis available")
        # Translate to Hindi
        hindi_text = await self.translate_to_hindi(final_sentiment)
        
        # Generate audio
        audio_path = self.generate_audio(hindi_text,company_name,"hi")
        
        # Add to the sentiment data
        result = sentiment_data.copy()
        result["Hindi_Translation"] = hindi_text
        result["Audio_Path"] = audio_path
        
        return result 