import traceroute
import socket
import requests
import folium
from folium.plugins import AntPath
import os
import re

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


def get_route_names(file_path):
    route_names = []

    with open(file_path, 'r', encoding='UTF-8') as file:
        for line in file:
            if '#### Running traceroute from' in line:
                match = re.search(r'to ([\d\.]+) \(([^,]+), ([^)]+)\)', line)
                if match:
                    dest_ip, dest_city, dest_country = match.groups()
                    route_name = f"{dest_city}, {dest_country} ({dest_ip})"
                    route_names.append(route_name)
                else:
                    route_names.append(f"route {len(route_names)}")

    return route_names


def draw_map_folium(selected_routes=None):
    for filename in os.listdir('reports/'):
        file_path = os.path.join('reports', filename)

        # read by section
        routes = []
        current_route = []
        route_names = get_route_names(f'reports/{filename[:-3]}.md')

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

        # if only collecting routes, return them
        if selected_routes is None:
            return routes, route_names

        # create a new map
        antalya_lat = 36.8969
        antalya_lon = 30.7133
        m = folium.Map(location=[antalya_lat, antalya_lon], zoom_start=3)

        colors = [
            '#39FF14', '#FF1493', '#00FFFF', '#FF6600', '#FFFF00',
            '#FF0000', '#14F0FF', '#FF00FF', '#7FFF00', '#FFA500',
            '#1E90FF', '#32CD32', '#FF69B4', '#00FF7F', '#FFD700',
            '#8A2BE2', '#00BFFF', '#FF4500', '#F0FF14', '#FF3131'
        ]

        # check how many routes are drawn
        routes_drawn = 0

        # only process routes explicitly selected
        for i, (route, name) in enumerate(zip(routes, route_names)):
            if name not in selected_routes:
                continue

            routes_drawn += 1
            color = colors[routes_drawn % len(colors)]
            line_offset = routes_drawn * 0.0005  # Use routes_drawn instead of i

            # process this route
            points = []
            for j, location in enumerate(route):
                lat = location["Latitude"] + line_offset
                lon = location["Longitude"] + line_offset

                if j == 0:  # starting point
                    folium.Marker(
                        [lat + 0.00002, lon + 0.00002],
                        tooltip=f"{location['City']}, {location['Country']} (Starting Point)",
                        icon=folium.Icon(color='green', icon='play', prefix='fa')
                    ).add_to(m)
                elif j == len(route) - 1:  # destination
                    folium.Marker(
                        [lat + 0.00002, lon + 0.00002],
                        tooltip=f"{location['City']}, {location['Country']} (Destination)",
                        icon=folium.Icon(color='black', icon='star', prefix='fa')
                    ).add_to(m)
                else:  # hop points
                    folium.Marker(
                        [lat, lon],
                        tooltip=f"{location['City']}, {location['Country']}"
                    ).add_to(m)

                points.append((lat, lon))

            # add the path if we have enough points
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

        if routes_drawn > 0:
            m.save(f"report_maps/map_{os.path.splitext(filename)[0]}.html")

    return True  # successfully processed


def create_route_selector():
    from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                                QCheckBox, QPushButton, QScrollArea, QLabel, QFrame)
    import sys

    # Get available routes
    routes, route_names = draw_map_folium(None)

    # Create application
    app = QApplication(sys.argv)

    # Create main window
    window = QMainWindow()
    window.setWindowTitle("Route Selector")
    window.setGeometry(100, 100, 600, 500)

    # Create central widget and layout
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    main_layout = QVBoxLayout(central_widget)

    # Create scrollable area
    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    main_layout.addWidget(scroll_area)

    # Create content widget for the scroll area
    content_widget = QWidget()
    scroll_area.setWidget(content_widget)
    layout = QVBoxLayout(content_widget)

    # Dictionary to hold checkbox objects
    check_boxes = {}

    # Add checkboxes for each route
    for i, name in enumerate(route_names):
        checkbox = QCheckBox(name)
        checkbox.setChecked(True)  # Default selected
        layout.addWidget(checkbox)
        check_boxes[name] = checkbox

    # Add render button
    render_btn = QPushButton("Render Selected Routes")
    main_layout.addWidget(render_btn)

    # Add status label
    status_label = QLabel("")
    main_layout.addWidget(status_label)

    # Function to render selected routes
    def render_selected():
        selected = [name for name, checkbox in check_boxes.items() if checkbox.isChecked()]
        if selected:
            draw_map_folium(selected)
            status_label.setText("Map rendered successfully!")
        else:
            status_label.setText("Please select at least one route")

    render_btn.clicked.connect(render_selected)

    window.show()

    # Start the event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    create_route_selector()
