import traceroute
import socket
import requests
import folium
from folium.plugins import AntPath
import os

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


def draw_map_folium():
    for filename in os.listdir('reports/'):
        file_path = os.path.join('reports', filename)

        # read by section
        routes = []
        current_route = []

        # create a map centered around Antalya
        antalya_lat = 36.8969
        antalya_lon = 30.7133
        m = folium.Map(location=[antalya_lat, antalya_lon], zoom_start=3)

        with open(file_path, 'r', encoding='UTF-8') as file:
            in_traceroute_section = False

            for line in file:
                if '#### Running traceroute from' in line:  # new traceroute section
                    if current_route:
                        routes.append(current_route)
                    current_route = []  # start new route
                    in_traceroute_section = True

                elif in_traceroute_section and '#' not in line and line.strip():
                    data = line.strip().split(",")
                    data = [item.strip() for item in data]
                    if len(data) == 5:
                        lat, lon, city, region, country = data
                        try:
                            current_route.append({
                                "Latitude": float(lat),
                                "Longitude": float(lon),
                                "City": city,
                                "Region": region,
                                "Country": country
                            })
                        except ValueError:
                            continue

        # add last route
        if current_route:
            routes.append(current_route)

        colors = [
            '#39FF14', '#FF1493', '#00FFFF', '#FF6600', '#FFFF00',
            '#FF0000', '#14F0FF', '#FF00FF', '#7FFF00', '#FFA500',
            '#1E90FF', '#32CD32', '#FF69B4', '#00FF7F', '#FFD700',
            '#8A2BE2', '#00BFFF', '#FF4500', '#F0FF14', '#FF3131'
        ]

        for i, route in enumerate(routes):
            color = colors[i % len(colors)]

            # markers for each location
            for j, location in enumerate(route):
                if j == 0:  # starting point
                    folium.Marker(
                        location=[location["Latitude"] + 0.001, location["Longitude"] + 0.001],
                        tooltip=f"{location['City']}, {location['Country']} (Starting Point)",
                        icon=folium.Icon(color='green', icon='play', prefix='fa')
                    ).add_to(m)
                elif j == len(route) - 1:  # destination
                    folium.Marker(
                        location=[location["Latitude"] + 0.001, location["Longitude"] + 0.001],
                        tooltip=f"{location['City']}, {location['Country']} (Destination)",
                        icon=folium.Icon(color='black', icon='star', prefix='fa')
                    ).add_to(m)
                else:  # intermediate hops
                    folium.Marker(
                        location=[location["Latitude"], location["Longitude"]],
                        tooltip=f"{location['City']}, {location['Country']}"
                    ).add_to(m)

            # lines
            points = [(location["Latitude"], location["Longitude"]) for location in route]
            if len(points) >= 2:
                AntPath(
                    locations=points,
                    color=color,
                    weight=3.5,
                    opacity=1.0,
                    delay=2000,
                    dash_array=[5, 15],
                    pulse_color='white',
                    hardwareAcceleration=True
                ).add_to(m)

        m.save(f"report_maps/map_{os.path.splitext(filename)[0]}.html")


if __name__ == "__main__":
    get_locations()
    draw_map_folium()

# de rulat din mai multe locatii, VPS, facultate, acasa, etc.
