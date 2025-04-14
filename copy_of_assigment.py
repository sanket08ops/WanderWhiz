import streamlit as st
import os
import requests
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_tavily import TavilySearch
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="WanderWhiz - Travel AI", layout="centered")

st.title("🌍 WanderWhiz - Your AI Travel Buddy")

# Sidebar for keys
with st.sidebar:
    st.header("🔐 API Keys Configuration")
    weather_api_key = st.text_input("🌦️ WeatherAPI Key", type="password")
    tavily_api_key = st.text_input("🔍 Tavily API Key", type="password")
    google_api_key = st.text_input("🤖 Google GenAI API Key", type="password")
    submit_keys = st.button("✅ Save API Keys")

if submit_keys:
    os.environ["WEATHER_API_KEY"] = WEATHER_API_KEY
    os.environ["TAVILY_API_KEY"] = tavily_api_key
    os.environ["GOOGLE_API_KEY"] = google_api_key
    st.success("✅ Keys saved! You can now ask about a place below.")

# Only allow travel query after all keys are present
if all([weather_api_key, tavily_api_key, google_api_key]):
    location = st.text_input("📍 Where are you planning to go?", placeholder="e.g., Paris, Tokyo, Mumbai")

    # Define WeatherAPI tool
    @tool
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather from WeatherAPI.
        """
        api_key = os.environ.get("WEATHER_API_KEY", "")
        if not api_key:
            return {"error": "Missing Weather API Key"}

        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={WEATHER_API_KEY}&units=metric"
        try:
            response = requests.get(url)
            data = response.json()

            if "error" in data:
                return {"error": data["error"]["message"]}

            current = data["current"]
            location_data = data["location"]
            return {
                "location": f"{location_data['name']}, {location_data['country']}",
                "temperature_c": current["temp_c"],
                "condition": current["condition"]["text"],
                "humidity": current["humidity"],
                "wind_kph": current["wind_kph"]
            }

        except Exception as e:
            return {"error": str(e)}

    # Init tools
    search_tool = TavilySearch(max_results=3)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    tools = [get_weather, search_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])
    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    if location:
        with st.spinner("✈️ Planning your trip..."):
            result = agent_executor.invoke({"input": f"Tell me the current weather and top attractions in {location}."})

        st.subheader("🗺️ Travel Summary")
        st.write(result.get("output", "Sorry, something went wrong."))

else:
    st.warning("Please enter all API keys in the sidebar to start your travel planning.")
