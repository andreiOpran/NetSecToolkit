import traceroute
import socket
import pandas as pd
import plotly.graph_objects as go
import requests
import folium

# domenii de test
domains = {
    'Asia': 'iij.ad.jp',
    'Europe': 'francetelevisions.fr',
    'NorthAmerica': 'cloudflare.com',
    'Australia1': 'telstra.com.au',
    'Australia2': 'sydney.edu.au',
    'SouthAfrica': 'seacom.mu',
    'Google': 'google.com',
    'DNS1': 'dns.adguard-dns.com'
}


# functie pentru a obtine IP-ul public
def get_local_machine_ip():
    response = requests.get("https://api.ipify.org?format=json")
    if response.status_code == 200:
        return response.json().get("ip")
    else:
        print(f"Error retrieving public IP: {response.status_code}")
        return None


# functie pentru a obtine IP-ul unui domeniu
def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def get_locations():
    # obtinem IP-ul local al masinii care ruleaza scriptul
    local_machine_ip = get_local_machine_ip()
    if local_machine_ip:
        local_machine_ip_location, local_machine_ip_city, local_machine_ip_region, local_machine_ip_country = traceroute.get_ip_info(local_machine_ip)
        with open(f"reports/{local_machine_ip}_{local_machine_ip_city}_{local_machine_ip_country}.md", "a") as file:
            file.write(f"# From machine with IP: {local_machine_ip} ({local_machine_ip_city}, {local_machine_ip_country})\n")
    else:
        print("Nu s-a putut obtine IP-ul public.")
    # iterare pe domenii
    for region, domain in domains.items():
        destination_ip = get_ip(domain)
        _, destination_ip_city, _, destination_ip_country = traceroute.get_ip_info(destination_ip)
        with open(f"reports/{local_machine_ip}_{local_machine_ip_city}_{local_machine_ip_country}.md", "a") as file:
            file.write(f"\n#### Running traceroute from {local_machine_ip} ({local_machine_ip_city}, {local_machine_ip_country}) "
                       f"to {destination_ip} ({destination_ip_city}, {destination_ip_country})\n")
            # write the starting location info to the file
            file.write(f'{local_machine_ip_location}, {local_machine_ip_city}, {local_machine_ip_region}, {local_machine_ip_country}  \n')
        if destination_ip:
            traceroute.traceroute(destination_ip, 33434, file_output=f"reports/{local_machine_ip}_{local_machine_ip_city}_{local_machine_ip_country}.md")


def draw_map_plotly():
    locations = []
    with open("reports/report.md", "r", encoding="UTF-8") as file:
        for line in file:
            if '#' not in line:  # verificam daca linia contine datele necesare
                data = line.strip().split(",")
                data = [item.strip() for item in data]  # eliminam spatiile albe
                if len(data) == 5:  # consideram formatul lat, lon, city, region, country
                    lat, lon, city, region, country = data
                    print(lat, lon, city, region, country)
                    locations.append({
                        "Latitude": float(lat),
                        "Longitude": float(lon),
                        "City": city,
                        "Region": region,
                        "Country": country
                    })

    # cream un dataframe din datele colectate
    df = pd.DataFrame(locations)

    fig = go.Figure()
    
    fig.add_trace(go.Scattergeo(
        lat=df['Latitude'],
        lon=df['Longitude'],
        mode='lines+markers+text',  # afisare linii, puncte si text
        text=df['City'],
        textposition='top center',  # pozitionare text
        line=dict(width=1, color='black'),  # grosime si culoare linie
        marker=dict(
            size=15,                # marimea punctelor
            color='red',            # culoarea punctelor
            symbol='circle',
            line=dict(
                width=1.5,            # grosimea conturului
                color='black'       # culoarea conturului
            )
        ),
        hoverinfo='text'
    ))
    
    fig.update_layout(
        title="Rutele prin diverse tari",
        geo=dict(   
            scope='world',  # harta globala
            projection_type='equirectangular',  # tipul proiectiei
            showland=True,  # afisare teren
            landcolor="rgb(229, 229, 229)",  # culoarea terenului
            countrycolor="rgb(255, 255, 255)"  # culoarea tarii
        )
    )

    # salvam harta ca fisier HTML
    fig.write_html("raport_harta_plotly.html")


def draw_map_folium():
    locations = []
    with open("reports/report.md", "r", encoding="UTF-8") as file:
        for line in file:
            if '#' not in line:
                data = line.strip().split(",")
                data = [item.strip() for item in data]
                if len(data) == 5:
                    lat, lon, city, region, country = data
                    try:
                        locations.append({
                            "Latitude": float(lat),
                            "Longitude": float(lon),
                            "City": city,
                            "Region": region,
                            "Country": country
                        })
                    except ValueError:
                        continue

    # Create a map centered around Antalya
    antalya_lat = 36.8969
    antalya_lon = 30.7133
    m = folium.Map(location=[antalya_lat, antalya_lon], zoom_start=3)

    # Add markers for each location
    for location in locations:
        folium.Marker(
            location=[location["Latitude"], location["Longitude"]],
            tooltip=f"{location['City']}, {location['Country']}"
        ).add_to(m)

    # Add lines connecting points
    points = [(location["Latitude"], location["Longitude"]) for location in locations]
    folium.PolyLine(points, color="red", weight=2.5, opacity=0.8).add_to(m)

    m.save("raport_harta_folium.html")


if __name__ == "__main__":
    # get_locations()
    draw_map_folium()

# de rulat din mai multe locatii, VPS, facultate, acasa, etc.
