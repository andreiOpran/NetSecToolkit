import traceroute
import socket
import pandas as pd
import plotly.express as px
import requests

# domenii de test
domains = {
    'Asia' : 'baidu.com',
    # 'Africa': 'gov.za',
    # 'Australia': 'gov.au'
}

# functie pentru a obtine IP-ul public
def get_public_ip():
    try:
        response = requests.get("https://api.ipify.org?format=json")
        if response.status_code == 200:
            return response.json().get("ip")
        else:
            print(f"Eroare la obținerea IP-ului public: {response.status_code}")
            return None
    except requests.RequestException as e:
        print(f"Eroare la conectarea la serviciul de IP public: {e}")
        return None

# functie pentru a obtine IP-ul unui domeniu
def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None

def get_locations():
    # obtinem IP-ul local al masinii care ruleaza scriptul
    public_ip = get_public_ip()
    if public_ip:
        with open("../raport.txt", "a") as file:
            file.write(f"Locatiile pentru mai multe regiuni de pe ip-ul {public_ip}\n")
    else:
        print("Nu s-a putut obtine IP-ul public.")
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