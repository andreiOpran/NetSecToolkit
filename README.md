# NetSecToolkit

A collaborative networking security toolkit developed by a team of 3, featuring comprehensive network analysis, DNS tunneling, traceroute visualization, and security demonstration tools. This project includes real-world implementations of network protocols and security concepts.

## Project Overview

NetSecToolkit is a comprehensive collection of networking tools and security implementations that demonstrate various network protocols and security concepts. As part of this project, we deployed DNS Pi-hole on our routers and successfully blocked over 40,000 advertisements, showcasing practical network security applications.

## Features

- **TCP Server**: Basic TCP server implementation with comprehensive logging
- **DNS Tunneling**: Covert file transfer over DNS protocol with integrity verification
- **Traceroute Analysis**: Global network path visualization with geographic mapping
- **ARP Spoofing**: Network security demonstration and man-in-the-middle attack simulation
- **Router Configuration**: Advanced iptables configuration for network routing and security
- **DNS Ad Blocking**: Pi-hole implementation blocking 40k+ advertisements

## Project Structure

```
src/
├── tcp_server.py           # Basic TCP server implementation
├── router.sh              # Network routing and security configuration
├── dns/                   # DNS tunneling and analysis tools
│   ├── udp_client.py      # DNS tunneling client implementation
│   ├── md5check.py        # File integrity verification tool
│   └── tunnel_files/      # Sample files for tunneling demonstrations
├── traceroute/            # Network path analysis toolkit
│   ├── traceroute.py      # Custom traceroute implementation
│   ├── report.py          # Automated report generation
│   ├── ai_report_selection_ui.py  # Interactive route visualization
│   └── reports/           # Generated global traceroute reports
└── arp_spoofing/          # ARP spoofing security demonstration
    ├── arp_spoofing.py    # ARP spoofing implementation
    └── instructions.md    # Detailed usage instructions
```

## Installation

### Prerequisites
- Python 3.7+
- Scapy library for packet manipulation
- Docker (for ARP spoofing demonstrations)
- Root privileges (required for raw socket operations)
- Linux environment (recommended for full functionality)

### Setup
```bash
git clone https://github.com/andreiOpran/NetSecToolkit.git
cd NetSecToolkit
pip install scapy netfilterqueue requests folium
```

## Usage Guide

### TCP Server
Simple TCP server demonstrating basic network communication:

```bash
cd src
python tcp_server.py
```

The server operates on `localhost:10000` and provides detailed logging of all connections and message exchanges.

### DNS Tunneling System

#### Client Operation
Perform covert file transfer through DNS protocol:

```bash
cd src/dns
python udp_client.py
```

Key features:
- Base64 encoding for binary data transmission
- Stop-and-wait protocol for reliability
- Automatic file reconstruction and validation
- Configurable DNS server endpoints and timeout handling

#### File Integrity Verification
Verify the integrity of transferred files:

```bash
python md5check.py example
```

This tool compares `tunnel_files/example.txt` with `received_files/example_received.txt` using MD5 hashing.

### Traceroute Analysis System

#### Basic Network Path Analysis
```bash
cd src/traceroute
python traceroute.py
```

#### Comprehensive Geographic Reporting
```bash
python report.py
```

#### Interactive Route Visualization
```bash
python ai_report_selection_ui.py
```

Features include:
- Real-time geographic IP location mapping
- Multi-destination network analysis
- Interactive route visualization with Folium
- Global network infrastructure analysis

### ARP Spoofing Security Demonstration

**Warning**: This tool is designed for educational purposes and controlled security testing environments only.

#### Environment Setup
```bash
cd src/arp_spoofing
# Follow detailed instructions in instructions.md
```

#### Demonstration Workflow
1. **Terminal 1**: Execute ARP spoofing script for network interception
2. **Terminal 2**: Monitor network traffic using tcpdump
3. **Terminal 3**: Generate target network traffic for analysis

## Global Network Analysis

Our comprehensive traceroute analysis includes data from multiple international locations:

- **Romania**: Constanța, Bucharest
- **India**: Doddaballapura
- **Australia**: Sydney
- **United States**: Santa Clara, San Francisco
- **Germany**: Frankfurt am Main

Each analysis provides:
- Complete network path with detailed hop-by-hop analysis
- Geographic coordinates and location data for each network hop
- Comprehensive city, region, and country information
- Interactive map visualization of global network routes

## Technical Implementation Details

### DNS Tunneling Protocol Specification
- **Data Encoding**: Base64 encoding for reliable binary data transmission
- **Transport Protocol**: DNS TXT record queries and responses
- **Domain Naming Convention**: `chunk{index}.{filename}.tunnel.broski.software`
- **Reliability Mechanism**: Stop-and-wait protocol with comprehensive timeout handling

### Traceroute Implementation Architecture
- **Methodology**: UDP packet transmission with incremental TTL values
- **ICMP Response Handling**: Time Exceeded and Destination Unreachable message processing
- **Geolocation Integration**: IPinfo.io API for real-time location data
- **Visualization Framework**: Folium-based interactive mapping with route plotting

### ARP Spoofing Security Mechanism
- **Target Strategy**: Gateway impersonation through ARP table manipulation
- **Attack Vector**: Gratuitous ARP reply injection
- **Traffic Interception**: NetfilterQueue integration for packet capture
- **Network Restoration**: Automated network healing procedures on termination

## DNS Ad Blocking Implementation

As part of our comprehensive network security approach, we implemented Pi-hole DNS filtering on our routers, achieving:
- **40,000+ blocked advertisements** across multiple devices
- Improved network performance through reduced bandwidth usage
- Enhanced privacy protection through tracking domain blocking
- Custom blocklist management and whitelist configuration

## Network Security Configuration

### Advanced Router Setup
```bash
sudo ./src/router.sh
```

This configuration script implements:
- TCP RST packet filtering for custom connection handling
- IP masquerading and NAT configuration
- Advanced iptables rules for traffic redirection and security

## Sample Outputs and Results

### Traceroute Analysis Example
```
Hop 1: 192.168.1.1 (Local Gateway) - 2.34 ms
Hop 2: 10.0.0.1 (ISP Regional Router) - 15.67 ms
Hop 3: 203.0.113.1 (International Hub) - 45.23 ms
Destination reached: Target Server - 120.45 ms
```

### DNS Tunneling Transfer Example
```
Received chunk 1: This is an example file...
Received chunk 2: for DNS tunneling demonst...
Received chunk 3: ration purposes only...
Downloaded file at "received_files/example_received.txt".
MD5 verification: Files are identical.
Transfer completed successfully.
```

## Security Considerations and Best Practices

- **ARP Spoofing Tools**: Strictly for controlled educational environments and authorized security testing
- **DNS Tunneling**: Ensure compliance with DNS provider terms of service and local regulations
- **Administrative Privileges**: Raw socket operations require root access for proper functionality
- **Network Performance**: Monitor network impact during testing and analysis operations
- **Legal Compliance**: Ensure all testing is conducted within legal boundaries and with proper authorization

## Collaborative Development

This project was developed collaboratively by a team of 3 students, combining expertise in:
- Network protocol analysis and implementation
- Security research and ethical hacking techniques
- Geographic data visualization and network mapping
- DNS infrastructure and traffic analysis

## Educational Resources and References

- [Scapy Documentation and Tutorials](https://scapy.net/)
- [RFC 1035 - Domain Name System Protocol](https://tools.ietf.org/html/rfc1035)
- [RFC 826 - Address Resolution Protocol](https://tools.ietf.org/html/rfc826)
- [IPinfo.io Geolocation API Documentation](https://ipinfo.io/)
- [Pi-hole Network-wide Ad Blocking](https://pi-hole.net/)

## Project Team

Developed collaboratively by [@andreiOpran](https://github.com/andreiOpran), [@alex6damian](https://github.com/alex6damian) and [@AlexHornet76](https://github.com/AlexHornet76).

This project serves educational and research purposes in network security and protocol analysis. Always ensure proper authorization and ethical guidelines when using these tools in any network environment.
