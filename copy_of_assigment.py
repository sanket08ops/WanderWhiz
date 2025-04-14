import os
import streamlit as st
import requests
from typing import Dict, Any

from langchain_core.tools import tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

# ─────────────────────────────────────────────
# 🌐 App Layout
# ─────────────────────────────────────────────
st.set_page_config(page_title="WanderWhiz 🌍", layout="centered")
st.markdown("<h1 style='text-align: center;'>✈️ WanderWhiz: Your Smart Travel Buddy</h1>", unsafe_allow_html=True)
st.markdown("#### Let AI plan your journey with weather and attractions insights!")

# ─────────────────────────────────────────────
# 🔑 Sidebar: Enter API Keys
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("🔐 Enter API Keys")

    weather_api_key = st.text_input("🌦️ OpenWeatherMap API Key", type="password")
    tavily_api_key = st.text_input("🔎 Tavily API Key", type="password")
    google_api_key = st.text_input("🧠 Google GenAI API Key", type="password")

    if st.button("✅ Save Keys"):
        st.session_state["weather_api_key"] = weather_api_key
        st.session_state["tavily_api_key"] = tavily_api_key
        st.session_state["google_api_key"] = google_api_key
        st.success("✅ API keys saved! You can now enter a destination.")

# ─────────────────────────────────────────────
# 🧰 Weather Tool
# ─────────────────────────────────────────────
@tool
def get_weather(location: str) -> Dict[str, Any]:
    """Get current weather for a location."""
    try:
        key = st.session_state.get("weather_api_key", "")
        if not key:
            return {"error": "Weather API key not provided."}

        url = f"http://api.openweathermap.org/data/2.5/weather?q={location}&appid={key}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return {"error": f"API Error: {data.get('message', 'Location not found')}"}

        return {
            "location": location,
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
            "wind_speed": data["wind"]["speed"]
        }

    except Exception as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────
# 🧠 Set Up AI Agent (if all keys are present)
# ─────────────────────────────────────────────
if all(k in st.session_state for k in ("weather_api_key", "tavily_api_key", "google_api_key")):
    os.environ["TAVILY_API_KEY"] = st.session_state["tavily_api_key"]
    os.environ["GOOGLE_API_KEY"] = st.session_state["google_api_key"]

    search_tool = TavilySearchResults(k=3)
    llm = ChatGoogleGenerativeAI(model="gemini-2.0", temperature=0)

    tools = [get_weather, search_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    agent = create_tool_calling_agent(llm=llm, tools=tools, prompt=prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    # ─────────────────────────────────────────────
    # 📍 Destination Input
    # ─────────────────────────────────────────────
    with st.container():
        st.subheader("📍 Where are you planning to go?")
        destination = st.text_input("Enter a city or place name", placeholder="e.g. Paris, Tokyo, Goa")

        if st.button("🌍 Plan My Trip"):
            with st.spinner("⏳ Planning your journey..."):
                try:
                    result = agent_executor.invoke(
                        {"input": f"Tell me the current weather and top attractions in {destination}"}
                    )
                    st.success("✨ Here's your travel info!")
                    st.markdown("#### 🗺️ Results")
                    st.write(result["output"])
                except Exception as e:
                    st.error(f"❌ Oops! Something went wrong: {e}")
else:
    st.info("ℹ️ Please enter and save all API keys from the sidebar to continue.")

