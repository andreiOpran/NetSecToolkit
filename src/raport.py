import traceroute
import socket
import pandas as pd
import plotly.express as px

# domenii de test
domains = {
    'Asia' : 'baidu.com',
    # 'Africa': 'gov.za',
    # 'Australia': 'gov.au'
}

# functie pentru a obtine IP-ul unui domeniu
def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def get_locations():
    # obtinem IP-ul local al masinii care ruleaza scriptul
    local_ip = socket.gethostbyname(socket.gethostname())
    with open("../raport.txt", "a") as file:
        file.write(f"Locatiile pentru mai multe regiuni de pe ip-ul {local_ip}\n")

    # iterare pe domenii
    for region, domain in domains.items():
        ip = get_ip(domain)
        if ip:
            traceroute.traceroute(ip, 33434)
    
    # desenam harta
    draw_map()

def draw_map():
    locations = []
    with open("../raport.txt", "r") as file:
        for line in file:
            if ',' in line: # verificam daca linia contine datele necesare
                data = line.strip().split(",")
                data = [item.strip() for item in data]  # eliminam spatiile albe
                if len(data) == 5:  # consideram formatul lat, lon, city, region, country
                    lat, lon, city, region, country = data
                    locations.append({
                        "Latitude": float(lat),
                        "Longitude": float(lon),
                        "City": city,
                        "Region": region,
                        "Country": country
                    })

    # cream un dataframe din datele colectate
    df = pd.DataFrame(locations)

    # generam harta
    fig = px.scatter_geo(
        df,
        lat="Latitude",
        lon="Longitude",
        text="City",
        hover_name="Country",
        title="Rutele prin diverse tari"
    )

    # salvam harta ca fisier HTML
    fig.write_html("../raport_harta.html")

if __name__ == "__main__":
    get_locations()

# de rulat din mai multe locatii, VPS, facultate, acasa, etc.