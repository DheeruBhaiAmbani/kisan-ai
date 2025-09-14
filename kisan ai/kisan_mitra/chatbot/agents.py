import os
import requests
import json
from django.conf import settings
from langchain.agents import AgentExecutor, create_json_agent
from langchain.llms import GoogleGenerativeAI
from langchain_community.chat_models import ChatGoogleGenerativeAI
from langchain.tools import tool, Tool
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
# from langchain_google_genai import GoogleGenerativeAIEmbeddings # For RAG
# from langchain.vectorstores import PGVector # If using pgvector explicitly

# Dummy ML model for crop recommendation (replace with actual joblib load)
class CropRecommendationModel:
    def predict(self, N, P, K, temperature, humidity, ph, rainfall):
        # In a real scenario, this would load a joblib model and predict
        # For conceptual:
        if 70 < N < 100 and 30 < P < 60 and 20 < K < 40 and 20 < temperature < 30:
            return "Rice"
        elif 80 < N < 110 and 15 < P < 30 and 40 < K < 60:
            return "Wheat"
        else:
            return "General crop (needs more data)"

crop_model = CropRecommendationModel()

# --- Define Tools for Agents ---

@tool
def get_weather_forecast(pin_code: str) -> str:
    """Fetches current weather forecast, temperature, humidity for a given Indian pincode."""
    api_key = settings.OPENWEATHER_API_KEY
    if not api_key:
        return "Weather API key not configured."
    try:
        # OpenWeatherMap sometimes uses city/zip. For Indian pincodes, cross-referencing is needed or use a different API.
        # For simplicity, simulating with a city lookup or generic response.
        # A more robust solution involves a geo-coding API to convert pin_code to lat/lon.
        # Let's assume a mapping or a direct city name for now.
        if pin_code == '110001': # Example for Delhi
            city_name = "Delhi,IN"
        elif pin_code == '400001': # Example for Mumbai
            city_name = "Mumbai,IN"
        else:
            city_name = "India" # Fallback or error

        url = f"http://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={api_key}&units=metric"
        response = requests.get(url)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        
        main_data = data.get('main', {})
        weather_description = data.get('weather', [{}])[0].get('description', 'N/A')
        temp = main_data.get('temp', 'N/A')
        humidity = main_data.get('humidity', 'N/A')
        
        return f"Weather in {city_name} (pin code {pin_code}): {weather_description}, Temperature: {temp}°C, Humidity: {humidity}%."
    except requests.exceptions.RequestException as e:
        return f"Error fetching weather forecast: {e}. Please ensure the pin code or API key is valid."


@tool
def get_market_prices(crop_name: str, location_pin_code: str = None) -> str:
    """Scrapes or looks up current market prices for a specific crop. Can be refined by location."""
    # This would involve actual web scraping (BeautifulSoup) or using an agriculture market API
    # For demonstration, a placeholder response:
    crop_prices = {
        "rice": {"delhi": "₹35/kg", "mumbai": "₹40/kg"},
        "wheat": {"delhi": "₹25/kg", "mumbai": "₹28/kg"},
        "tomato": {"delhi": "₹20/kg", "mumbai": "₹22/kg"},
    }
    crop_name_lower = crop_name.lower()
    
    if crop_name_lower in crop_prices:
        if location_pin_code:
            # Map pin_code to city for price lookup
            city_map = {'110001': 'delhi', '400001': 'mumbai'}
            city = city_map.get(location_pin_code, 'delhi') # Default to delhi
            price = crop_prices[crop_name_lower].get(city, "Price not available for this location.")
            return f"Current market price for {crop_name} in {city.capitalize()} (pin code {location_pin_code}): {price}"
        else:
            return f"Current market price for {crop_name}: Delhi: {crop_prices[crop_name_lower].get('delhi')}, Mumbai: {crop_prices[crop_name_lower].get('mumbai')}. Please provide a pin code for specific location."
    return f"Market prices for {crop_name} not available in our current data."

@tool
def recommend_crop(N: float, P: float, K: float, temperature: float, humidity: float, ph: float, rainfall: float) -> str:
    """Recommends a suitable crop based on N (Nitrogen), P (Phosphorus), K (Potassium) levels, temperature (°C), humidity (%), soil pH, and rainfall (mm).
       Example Usage: recommend_crop(90, 42, 43, 20.8, 82, 6.5, 202.9)
    """
    try:
        recommendation = crop_model.predict(N, P, K, temperature, humidity, ph, rainfall)
        return f"Based on the provided soil and environmental conditions, the recommended crop is: {recommendation}."
    except Exception as e:
        return f"Error in crop recommendation: {e}. Please check the input parameters."

@tool
def analyze_crop_image(image_url: str) -> str:
    """Analyzes an uploaded image of a crop to identify diseases or pests. Returns diagnosis and potential remedies."""
    # This would call an external API (e.g., Roboflow or a custom CV model deployed elsewhere)
    # For conceptual:
    if "leaf_spot" in image_url.lower(): # Simulate by filename if needed
        return "Diagnosis: Early Blight (Leaf Spot) on Tomato. Remedy: Apply copper-based fungicides, improve air circulation, remove infected leaves."
    elif "healthy" in image_url.lower():
        return "Diagnosis: Crop appears healthy. Continue regular monitoring."
    else:
        return "Unable to diagnose from the image. Please provide a clearer image or consult an expert."


# --- Define the multi-agent Orchestrator ---
class KisanMitraOrchestrator:
    def __init__(self, user_pin_code=None):
        self.llm = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.5, google_api_key=settings.GEMINI_API_KEY)
        self.user_pin_code = user_pin_code

        # List all available tools
        self.tools = [
            get_weather_forecast,
            get_market_prices,
            recommend_crop,
            analyze_crop_image,
            # Add more tools here (e.g., Knowledge Agent for RAG)
        ]

        # Define the agent executor
        # We use create_react_agent or create_json_agent for more structured output
        self.agent_executor = AgentExecutor.from_agent_and_tools(
            agent=create_json_agent(self.llm, self.tools, verbose=True), # Use JSON agent for structured tool calls
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True # Crucial for robustness
        )

    def process_query(self, query: str) -> str:
        """Processes a user query using the multi-agent system."""
        # Add user's pin code to the query context if available, to help agents
        context_query = query
        if self.user_pin_code:
            context_query = f"User is located in pin code {self.user_pin_code}. " + query
        
        try:
            # LangChain AgentExecutor will choose the best tool(s) based on the query
            response = self.agent_executor.invoke({"input": context_query})
            return response['output']
        except Exception as e:
            print(f"Error processing query with agent: {e}")
            return "I apologize, I encountered an error while processing your request. Could you please rephrase or try again later?"

# Example of how you might integrate a RAG (Retrieval Augmented Generation) tool
# For RAG, you'd need PGVector setup in Supabase and populate it with agricultural knowledge
# from langchain.vectorstores import PGVector
# from langchain.embeddings import GoogleGenerativeAIEmbeddings
# from langchain.chains import create_qa_chain
# @tool
# def knowledge_lookup(query: str) -> str:
#     """Looks up information from the agricultural knowledge base."""
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=settings.GEMINI_API_KEY)
#     CONNECTION_STRING = settings.DATABASE_URL
#     vectorstore = PGVector(
#         collection_name="agri_knowledge",
#         connection_string=CONNECTION_STRING,
#         embedding_function=embeddings,
#     )
#     docs = vectorstore.similarity_search(query, k=3)
#     # Use another LLM chain to synthesize the answer from retrieved docs
#     qa_chain = create_qa_chain(ChatGoogleGenerativeAI(model="gemini-pro", google_api_key=settings.GEMINI_API_KEY), chain_type="stuff")
#     response = qa_chain.invoke({"input_documents": docs, "question": query})
#     return response['output_text']
# # Add knowledge_lookup to self.tools in KisanMitraOrchestrator