import traceroute
import socket
import pandas as pd
import plotly.express as px
import requests

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
        with open("raport.md", "a") as file:
            file.write(f"\n\n\n# From machine with IP: {local_machine_ip} ({local_machine_ip_city}, {local_machine_ip_country})\n")
    else:
        print("Nu s-a putut obtine IP-ul public.")
    # iterare pe domenii
    for region, domain in domains.items():
        destination_ip = get_ip(domain)
        _, destination_ip_city, _, destination_ip_country = traceroute.get_ip_info(destination_ip)
        with open("raport.md", "a") as file:
            file.write(f"\n#### Running traceroute from {local_machine_ip} ({local_machine_ip_city}, {local_machine_ip_country}) "
                       f"to {destination_ip} ({destination_ip_city}, {destination_ip_country})\n")
            # write the starting location info to the file
            file.write(f'{local_machine_ip_location}, {local_machine_ip_city}, {local_machine_ip_region}, {local_machine_ip_country}  \n')
        if destination_ip:
            traceroute.traceroute(destination_ip, 33434)

    # desenam harta
    draw_map()


def draw_map():
    locations = []
    with open("raport.md", "r", encoding="UTF-8") as file:
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
    fig.write_html("raport_harta.html")


if __name__ == "__main__":
    # get_locations()
    draw_map()

# de rulat din mai multe locatii, VPS, facultate, acasa, etc.
