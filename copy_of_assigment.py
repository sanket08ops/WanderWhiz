import streamlit as st
import os
import requests
from typing import Dict, Any
from langchain_core.tools import tool
from langchain_tavily import TavilySearch
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

st.set_page_config(page_title="Travel Assistant", page_icon="🌍")

st.title("🌍 WONDERWIZ: AI Travel Assistant")

# Sidebar for API Keys
st.sidebar.header("🔑 API Keys")
google_api_key = st.sidebar.text_input("🔐 Enter your Google API Key", type="password")
tavily_api_key = st.sidebar.text_input("🔐 Enter your Tavily API Key", type="password")
weather_api_key = st.sidebar.text_input("🔐 Enter your Weather API Key", type="password")

# Location Input only after API keys are entered
if google_api_key and tavily_api_key and weather_api_key:
    # 🌍 Destination Input
    destination = st.text_input("📍 Where are you planning to go?")
else:
    st.warning("Please enter all API keys in the sidebar.")

# When user clicks the button
if st.button("Get Travel Info") and all([google_api_key, tavily_api_key, weather_api_key, destination]):
    # Set environment variables
    os.environ["GOOGLE_API_KEY"] = google_api_key
    os.environ["TAVILY_API_KEY"] = tavily_api_key
    WEATHER_API_KEY = weather_api_key

    # 🌤️ Custom weather tool
    @tool
    def get_weather(location: str) -> Dict[str, Any]:
        """
        Get current weather for a location.
        """
        try:
            url = f"http://api.weatherapi.com/v1/current.json?key={WEATHER_API_KEY}&q={location}"
            response = requests.get(url)
            data = response.json()

            if "error" in data:
                return {"error": data['error']['message']}

            weather = {
                "location": location,
                "temperature": data["current"]["temp_c"],
                "description": data["current"]["condition"]["text"],
                "humidity": data["current"]["humidity"],
                "wind_speed": data["current"]["wind_kph"]
            }
            return weather

        except Exception as e:
            return {"error": str(e)}

    # 🔍 Tavily search tool
    search_tool = TavilySearch(max_results=3)

    # 🤖 Gemini LLM
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

    # Tools and prompt
    tools = [get_weather, search_tool]
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful travel assistant."),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}")
    ])

    # Agent setup
    agent = create_tool_calling_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

    with st.spinner("Thinking... 🤔"):
        response = agent_executor.invoke({"input": f"Tell me the current weather and top attractions in {destination}."})
        
        st.subheader("✈️ Travel Assistant Result")
        
        # Check for weather info
        weather_info = get_weather(destination)
        if 'error' in weather_info:
            st.error(f"❌ Error fetching weather: {weather_info['error']}")
        else:
            st.markdown(f"**Weather in {weather_info['location']}**:\n")
            st.markdown(f"🌡️ Temperature: {weather_info['temperature']}°C\n")
            st.markdown(f"🌤️ Condition: {weather_info['description']}\n")
            st.markdown(f"💨 Wind Speed: {weather_info['wind_speed']} km/h\n")
            st.markdown(f"💧 Humidity: {weather_info['humidity']}%\n")

        # Show the agent's response for travel info
        if "output" in response:
            st.write(response["output"])

elif st.button("Get Travel Info"):
    st.warning("Please fill in all API keys and destination.")
