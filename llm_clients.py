import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMClient:
    """Base class for LLM API clients."""
    def __init__(self):
        self.provider = None
        self.model = None
        
    def generate(self, prompt, is_json=False):
        """Generate a response from the LLM."""
        raise NotImplementedError("Subclasses must implement this method")

class GroqClient(LLMClient):
    """Client for Groq API."""
    def __init__(self):
        super().__init__()
        self.provider = "groq"
        self.api_key = os.getenv("GROQ_API_KEY")
        self.model = os.getenv("LLM_MODEL", "llama3-70b-8192")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.api_key:
            raise ValueError("GROQ_API_KEY environment variable is not set")
            
    def generate(self, prompt, is_json=False):
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7
        }
        
        if is_json:
            data["response_format"] = {"type": "json_object"}
            
        response = requests.post(self.api_url, headers=headers, json=data)
        
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")
            
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        
        if is_json:
            return json.loads(content)
        return content

class OpenAIClient(LLMClient):
    """Client for OpenAI API."""
    def __init__(self):
        super().__init__()
        self.provider = "openai"
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        # Import here to avoid requiring the package if not used
        import openai
        self.client = openai.OpenAI(api_key=self.api_key)
            
    def generate(self, prompt, is_json=False):
        response_format = {"type": "json_object"} if is_json else None
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            response_format=response_format
        )
        
        content = response.choices[0].message.content
        
        if is_json:
            return json.loads(content)
        return content

class AnthropicClient(LLMClient):
    """Client for Anthropic API."""
    def __init__(self):
        super().__init__()
        self.provider = "anthropic"
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = os.getenv("LLM_MODEL", "claude-3-opus-20240229")
        
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        # Import here to avoid requiring the package if not used
        import anthropic
        self.client = anthropic.Anthropic(api_key=self.api_key)
            
    def generate(self, prompt, is_json=False):
        system_prompt = "Please provide a detailed response."
        if is_json:
            system_prompt = "Please provide a response in valid JSON format."
        
        response = self.client.messages.create(
            model=self.model,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7
        )
        
        content = response.content[0].text
        
        if is_json:
            return json.loads(content)
        return content

class GoogleAIClient(LLMClient):
    """Client for Google AI API."""
    def __init__(self):
        super().__init__()
        self.provider = "google"
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gemini-1.0-pro")
        
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        
        # Import here to avoid requiring the package if not used
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        self.model_obj = genai.GenerativeModel(self.model)
            
    def generate(self, prompt, is_json=False):
        if is_json:
            prompt = f"{prompt}\n\nImportant: Respond with only a valid JSON object, without any additional text or explanation."
            
        response = self.model_obj.generate_content(prompt)
        content = response.text
        
        if is_json:
            # Clean the response to ensure it's valid JSON
            # Some models might add markdown backticks or other text
            content = content.strip()
            if content.startswith("```json"):
                content = content.replace("```json", "", 1).strip()
            if content.startswith("```"):
                content = content.replace("```", "", 1).strip()
            if content.endswith("```"):
                content = content[:-3].strip()
                
            return json.loads(content)
        return content

def get_llm_client():
    """Factory function to get the appropriate LLM client based on environment variables."""
    if os.getenv("GROQ_API_KEY"):
        return GroqClient()
    elif os.getenv("OPENAI_API_KEY"):
        return OpenAIClient()
    elif os.getenv("ANTHROPIC_API_KEY"):
        return AnthropicClient()
    elif os.getenv("GOOGLE_API_KEY"):
        return GoogleAIClient()
    else:
        raise ValueError("No valid API key found in environment variables. Please set GROQ_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY.") 