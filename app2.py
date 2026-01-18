import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime



#function to get user's selection
def selectLocation(data):

    country_set = set(data.loc[:,"country"]) #Creating set with all countries
    country = st.selectbox('Select a country', options=country_set) #creating selectbox to select country

    country_data = data.loc[data.loc[:,"country"] == country,:]
    city_set = country_data.loc[:,"city_ascii"] #Getting the cities for the selected country
    city = st.selectbox('Select a city', options=city_set) #creating selectbox to select country

    #get the lat lon for the selection
    lat = float(country_data.loc[data.loc[:,"city_ascii"] == city, "lat"]) 
    lon = float(country_data.loc[data.loc[:,"city_ascii"] == city, "lng"])

    return country,city,lat,lon

#function to get weather data using open-mateo API 
def get_weather(lat, lon, past_days, forecast_days, variable, timezone, show_daily):
    base_url = "https://api.open-meteo.com/v1/forecast"

    #parameters to specify required data
    params = {
        "latitude": lat,
        "longitude": lon,
        "past_days": past_days,
        "forecast_days": forecast_days,
        "hourly": variable,
        "timezone": timezone,
        "current_weather": True,
    }

    #parameters to get daily data
    if show_daily:
        # Basic daily variables; you can add more
        params["daily"] = ["temperature_2m_max", "temperature_2m_min", "rain_sum", "snowfall_sum", "precipitation_sum", "windgusts_10m_max"]

    #Get the data in json
    resp = requests.get(base_url, params=params)
    resp.raise_for_status() #error handling. Stops proceeding if not get any response
    return resp.json() #Converts the response in json to python dictionary and returns that



st.set_page_config(page_title="Weather App", layout="wide")

st.title("Welcome to Ayaan's Weather App!! :sun_behind_rain_cloud:")

st.subheader("Choose a location :cityscape:")

#Reading location info from file
file = "worldcities.csv"
data = pd.read_csv(file)

country,city,lat,lon = selectLocation(data)

#creating sidebar on the page
with st.sidebar:
    st.header("Settings")

    st.write("Selected location: ", city, " in ", country)

    # creating sliders for the user to select number of past and future days to see weather trend
    past_days = st.slider("Past days (historical)", min_value=0, max_value=30, value=5)
    forecast_days = st.slider("Forecast days", min_value=1, max_value=16, value=5)

    #user to check this box if wants to see the trend of daily max/min temperature
    show_daily = st.checkbox("Show Daily Max/Min Temperature Trend)", value=False)

    #user to check this box if wants to see the trend of daily total_snowfall and total_rain
    show_daily2 = st.checkbox("Show Daily Total Snowfall and Rain Trend)", value=False)


try:
       variable="temperature_2m" 
       timezone="auto" #open-mateo will automatically detect the timezone from lat-lon
       wdata = get_weather(lat, lon, past_days, forecast_days, variable, timezone, show_daily)

        
       # Extract Hourly data
    
       hourly = wdata.get("hourly", {})
       if not hourly:
            st.error("No hourly data returned from API.")
       else:
            times = pd.to_datetime(hourly["time"])
            values = hourly[variable]

            #Create dataframe with hourly data (time and temperature)
            df_hourly = pd.DataFrame({
                "time": times,
                variable: values
            }).set_index("time")

            # Current weather
            current_weather = wdata.get("current_weather")
            current_time = None
            current_value = None

            if current_weather is not None:
                current_time = pd.to_datetime(current_weather["time"])
                current_value = current_weather.get("temperature")

except requests.HTTPError as e:
        st.error(f"HTTP error: {e}")
except Exception as e:
        st.error(f"Unexpected error: {e}")


#if user selects current weather button, then it will show current weather
if st.button("Current Weather"):
            st.info("Current weather is refreshed in every 15 minutes.")
            # Show some current info
            st.subheader("Current Weather")
            if current_weather:
                col1, col2, col3= st.columns(3)
                col1.metric("Time", str(current_weather["time"]))
                if "temperature" in current_weather:
                    col2.metric("Temperature (°C)", current_weather["temperature"])
                if "windspeed" in current_weather:
                    col3.metric("Wind speed (km/h)", current_weather["windspeed"])
                
            else:
                st.info("Current weather information not available in this response.")

#if user selects Show trend button
if st.button("Show Trend"):

            st.subheader("Hourly Trend (Historical + Forecast)")
            fig, ax = plt.subplots(figsize=(12, 5))

            var_label="temperature_2m"
            ax.plot(df_hourly.index, df_hourly[variable], label=var_label)

            # Add current point 
            if current_time is not None and current_value is not None:
                ax.scatter(current_time, current_value, s=60, marker="o", label="Current value")

            ax.set_xlabel("Time")
            ax.set_ylabel("Temperature")
            ax.set_title(f"Hourly temperature for past {past_days} days & next {forecast_days} days")
            ax.grid(True)
            ax.legend()
            fig.tight_layout()

            st.pyplot(fig)

            # Graph to show daily max-min temp trend
            if show_daily:
                 daily = wdata.get("daily", {})
                 if daily:
                      st.subheader("Daily Max/Min Temperature")
                      daily_time = pd.to_datetime(daily["time"])
                      df_daily = pd.DataFrame({
                              "date": daily_time,
                              "temp_max": daily["temperature_2m_max"],
                              "temp_min": daily["temperature_2m_min"]
                            }).set_index("date")

                      fig2, ax2 = plt.subplots(figsize=(12, 4))
                      ax2.plot(df_daily.index, df_daily["temp_max"], label="Max temp (°C)")
                      ax2.plot(df_daily.index, df_daily["temp_min"], label="Min temp (°C)")
                      ax2.set_xlabel("Date")
                      ax2.set_ylabel("Temperature (°C)")
                      ax2.set_title("Daily Temperature Max/Min")
                      ax2.grid(True)
                      ax2.legend()
                      fig2.tight_layout()

                      st.pyplot(fig2)

            #Graph to show daily total snow and rain 
            if show_daily2:
                 daily2 = wdata.get("daily", {})
                 if daily2:
                      st.subheader("Daily Total Snow/Rain")
                      daily_time2 = pd.to_datetime(daily["time"])
                      df_daily2 = pd.DataFrame({
                              "date": daily_time,
                              "total_snow": daily["snowfall_sum"],
                              "total_rain": daily["rain_sum"]
                            }).set_index("date")

                      fig22, ax22 = plt.subplots(figsize=(12, 4))
                      ax22.plot(df_daily2.index, df_daily2["total_snow"], label="total_snow")
                      ax22.plot(df_daily2.index, df_daily2["total_rain"], label="total_rain")
                      ax22.set_xlabel("Date")
                      ax22.set_ylabel("Total snow (cm)/rain (mm)")
                      ax22.set_title("Daily Total Snow/Rain")
                      ax22.grid(True)
                      ax22.legend()
                      fig22.tight_layout()

                      st.pyplot(fig22)
            
            
        
