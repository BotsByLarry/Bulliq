import requests
import json
import logging
from typing import List, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

class LLMService:
    """
    Handles streaming/non-streaming chat completions using a cascading LLM approach:
    Attempts to call OpenRouter first (with access to top models),
    falling back to Google Gemini AI Studio key if OpenRouter fails or is unconfigured.
    """
    
    def __init__(self):
        self.openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
        self.gemini_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent"
        
    async def get_chat_response(self, messages: List[Dict[str, str]], system_prompt: str) -> str:
        # Check if OpenRouter key is present
        if settings.OPENROUTER_API_KEY:
            try:
                logger.info("Attempting LLM call via OpenRouter (Primary)...")
                headers = {
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:3000", # Required by OpenRouter
                    "X-Title": "Bulliq AI Terminal"
                }
                
                # Combine system prompt with messages
                payload_messages = [{"role": "system", "content": system_prompt}] + messages
                
                payload = {
                    "model": "google/gemini-2.5-flash",  # High quality, extremely fast, cheap model
                    "messages": payload_messages,
                    "temperature": 0.7,
                    "max_tokens": 1500  # Specify token limits to stay under credit caps
                }
                
                res = requests.post(self.openrouter_url, headers=headers, json=payload, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data["choices"][0]["message"]["content"]
                    logger.info("OpenRouter response success.")
                    return response_text
                else:
                    logger.warning(f"OpenRouter returned status code {res.status_code}: {res.text}. Cascading to Gemini...")
            except Exception as e:
                logger.error(f"OpenRouter request failed: {str(e)}. Cascading to Gemini...")
                
        # Cascade/Fallback to Google Gemini API
        if settings.GEMINI_API_KEY:
            try:
                logger.info("Attempting LLM call via Google AI Studio (Fallback)...")
                # Format payload for Google's native API structure
                contents = []
                
                # Convert system prompt as first turn if possible or append to first user message
                contents.append({
                    "role": "user",
                    "parts": [{"text": f"SYSTEM SYSTEM GUIDELINES: {system_prompt}"}]
                })
                contents.append({
                    "role": "model",
                    "parts": [{"text": "Acknowledged. I will strictly follow all rules and guidelines provided."}]
                })
                
                for msg in messages:
                    role = "user" if msg["role"] == "user" else "model"
                    contents.append({
                        "role": role,
                        "parts": [{"text": msg["content"]}]
                    })
                    
                url_with_key = f"{self.gemini_url}?key={settings.GEMINI_API_KEY}"
                payload = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.7
                    }
                }
                
                res = requests.post(url_with_key, json=payload, timeout=15)
                if res.status_code == 200:
                    data = res.json()
                    response_text = data["candidates"][0]["content"]["parts"][0]["text"]
                    logger.info("Gemini response success.")
                    return response_text
                else:
                    logger.error(f"Gemini API returned status {res.status_code}: {res.text}")
            except Exception as e:
                logger.error(f"Gemini API request failed: {str(e)}")
                
        # Final static fallback if no keys configured or failed
        return (
            "Hello! I am your Bulliq AI Assistant. I notice that the LLM API Keys might be undergoing configuration. "
            "Please confirm your credentials inside your `.env` settings. "
            "In the meantime, I am happy to help you analyze market indicators and risk parameters!"
        )
