import pandas as pd
import numpy as np
import pvlib
import requests
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# ------------------ 1. User Inputs ------------------ #
latitude = float(input("Enter latitude: "))
longitude = float(input("Enter longitude: "))
tilt_angle = float(input("Enter collector tilt angle (degrees): "))
altitude = float(input("Enter site altitude above sea level (meters): "))
date = input("Enter date (YYYY-MM-DD): ")

# ------------------ 2. Generate Time Range (6 AM - 6 PM) ------------------ #
start_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=6)
end_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=18)
time_range = pd.date_range(start=start_time, end=end_time, freq='H', tz="UTC")

# ------------------ 3. Compute Solar Position & Radiation ------------------ #
location = pvlib.location.Location(latitude, longitude, altitude=altitude)
solar_position = location.get_solarposition(time_range)
clearsky = location.get_clearsky(time_range)

beam_radiation = clearsky['dni']  # Direct Normal Irradiance (W/m²)
diffuse_radiation = clearsky['dhi']  # Diffuse Horizontal Irradiance (W/m²)
global_radiation = clearsky['ghi']  # Global Horizontal Irradiance (W/m²)

# Compute reflected radiation based on surface albedo
albedo = 0.2  # Estimated ground reflectivity
reflected_radiation = albedo * global_radiation

# Compute total radiation on the tilted collector
total_radiation = beam_radiation + diffuse_radiation + reflected_radiation

# ------------------ 4. Display Results in a Table ------------------ #
results = pd.DataFrame({
    "Time": time_range.strftime("%H:%M"),
    "Beam Radiation (W/m²)": beam_radiation.values,
    "Diffuse Radiation (W/m²)": diffuse_radiation.values,
    "Reflected Radiation (W/m²)": reflected_radiation.values,
    "Total Radiation (W/m²)": total_radiation.values
})
print(results)

# ------------------ 5. Plot Radiation Data ------------------ #
plt.figure(figsize=(10, 5))
plt.plot(time_range, beam_radiation, label="Beam Radiation", linestyle='-', marker='o')
plt.plot(time_range, diffuse_radiation, label="Diffuse Radiation", linestyle='-', marker='s')
plt.plot(time_range, reflected_radiation, label="Reflected Radiation", linestyle='-', marker='d')
plt.plot(time_range, total_radiation, label="Total Radiation", linestyle='-', marker='x', linewidth=2)

plt.xlabel("Time")
plt.ylabel("Radiation (W/m²)")
plt.title("Solar Radiation Throughout the Day")
plt.legend()
plt.xticks(rotation=45)
plt.grid()
plt.show()
