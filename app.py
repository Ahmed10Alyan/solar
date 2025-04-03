from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import pvlib
import plotly.express as px
from datetime import datetime, timedelta

app = Flask(__name__)

# قائمة أنواع البطاريات وكفاءتها (متوسط القيم)
BATTERY_TYPES = {
    "Lead Acid": 85,
    "Lithium-ion": 95,
    "Nickel-Cadmium": 75,
    "Solid-State": 98
}

# دالة لحساب زاوية الميل المثلى
def optimal_tilt_angle(latitude, season="yearly"):
    if season == "summer":
        return latitude - 10
    elif season == "winter":
        return latitude + 10
    else:
        return latitude

# حساب الإشعاع الشمسي والطاقة المخزنة
def calculate_radiation(latitude, longitude, tilt_angle, altitude, date, efficiency, panel_area, battery_type):
    start_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=6)
    end_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=18)
    time_range = pd.date_range(start=start_time, end=end_time, freq='H', tz="UTC")

    location = pvlib.location.Location(latitude, longitude, altitude=altitude)
    solar_position = location.get_solarposition(time_range)
    clearsky = location.get_clearsky(time_range)

    dni_extra = pvlib.irradiance.get_extra_radiation(time_range)
    beam_radiation = clearsky['dni']
    diffuse_radiation = clearsky['dhi']
    global_radiation = clearsky['ghi']
    reflected_radiation = 0.2 * global_radiation
    total_radiation = beam_radiation + diffuse_radiation + reflected_radiation

    panel_output = (total_radiation * efficiency * panel_area) / 100
    energy_generated = panel_output.sum()

    # تحديد كفاءة البطارية حسب النوع
    battery_efficiency = BATTERY_TYPES.get(battery_type, 85)
    energy_stored = energy_generated * (battery_efficiency / 100)

    results = pd.DataFrame({
        "Time": time_range.strftime("%H:%M"),
        "Beam Radiation (W/m²)": beam_radiation.values,
        "Diffuse Radiation (W/m²)": diffuse_radiation.values,
        "Reflected Radiation (W/m²)": reflected_radiation.values,
        "Total Radiation (W/m²)": total_radiation.values,
        "Panel Output (W)": panel_output.values
    })

    fig = px.line(results, x="Time", y=["Beam Radiation (W/m²)", "Diffuse Radiation (W/m²)", "Reflected Radiation (W/m²)", "Total Radiation (W/m²)"])
    fig.update_layout(title="Solar Radiation Throughout the Day", xaxis_title="Time", yaxis_title="Radiation (W/m²)")
    graph_html = fig.to_html(full_html=False)
    
    return results, graph_html, energy_generated, energy_stored, battery_efficiency

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        try:
            latitude = float(request.form.get("latitude", 0) or 0)
            longitude = float(request.form.get("longitude", 0) or 0)
            altitude = float(request.form.get("altitude", 0) or 0)
            date = request.form.get("date", "2024-01-01")  
            efficiency = float(request.form.get("efficiency", 0) or 0)
            panel_area = float(request.form.get("panel_area", 1) or 1)

            season = request.form.get("season", "yearly")
            tilt_angle = float(request.form.get("tilt_angle") or optimal_tilt_angle(latitude, season))

            battery_type = request.form.get("battery_type", "Lead Acid")

            results, graph_html, energy_generated, energy_stored, battery_efficiency = calculate_radiation(
                latitude, longitude, tilt_angle, altitude, date, efficiency, panel_area, battery_type
            )
            
            return render_template("result.html", results=results.to_html(classes="table table-striped"),
                                   graph_html=graph_html, energy_generated=energy_generated, energy_stored=energy_stored,
                                   tilt_angle=tilt_angle, battery_type=battery_type, battery_efficiency=battery_efficiency)
        except ValueError as e:
            return f"خطأ في إدخال البيانات: {str(e)}"
    
    return render_template("index.html", battery_types=BATTERY_TYPES.keys())

if __name__ == "__main__":
    app.run(debug=True)
