import socket
import json
import os
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()
api_token = os.getenv('IPINFO_API_TOKEN')


def load_ip_info_cache(file_path='ip_info_cache.json'):
    if os.path.exists(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)
    return {}


def save_ip_info_cache(ip_info_cache, file_path='ip_info_cache.json'):
    with open(file_path, 'w') as file:
        json.dump(ip_info_cache, file, indent=4)


def get_ip(domain):
    try:
        return socket.gethostbyname(domain)
    except socket.gaierror:
        return None


def get_ip_info(ip_address, token=api_token, ip_info_cache=None):
    if ip_info_cache is None:
        ip_info_cache = {}

    if ip_address in ip_info_cache:
        return ip_info_cache[ip_address]

    try:
        response = requests.get(f'https://api.ipinfo.io/lite/{ip_address}?token={token}')
        if response.status_code == 200:
            data = response.json()
            ip_info_cache[ip_address] = data
            save_ip_info_cache(ip_info_cache)
            return data
        else:
            return None
    except requests.RequestException as e:
        print(f"Error fetching IP info for {ip_address}: {e}")
        return None


def extract_blocked_domains(file_path='../blocked_domains.md'):
    blocked_domains = []

    with open(file_path, 'r') as file:
        for line in file:
            if not line.strip():
                continue
            domain = line.split(' ')[0]
            blocked_domains.append(domain)
    return blocked_domains


def analyze_blocked_domains(blocked_domains):
    ip_info_cache = load_ip_info_cache()

    block_counts_for_each_company = defaultdict(int)
    company_of_origin_for_domain = defaultdict(list)
    requests_count = 0

    for domain in blocked_domains:
        # output for progress tracking
        requests_count += 1
        domain_info = f'Resolving domain: {domain}'
        print(f'{domain_info:<90}{requests_count}/{len(blocked_domains)}')

        ip_address = get_ip(domain)
        if ip_address:
            ip_info = get_ip_info(ip_address, api_token, ip_info_cache)
            if ip_info and 'as_name' in ip_info:
                company = ip_info['as_name']
                block_counts_for_each_company[company] += 1
                if domain not in company_of_origin_for_domain[company]:  # avoid duplicates
                    company_of_origin_for_domain[company].append(domain)

    save_ip_info_cache(ip_info_cache)

    blocked_companies_info = {
        'total_blocked_domains': len(blocked_domains),
        'block_counts_for_each_company': block_counts_for_each_company,
        'company_of_origin_for_domain': company_of_origin_for_domain
    }

    with open('blocked_companies_info.json', 'w') as file:
        json.dump(blocked_companies_info, file, indent=4)


if __name__ == "__main__":
    blocked_domains = extract_blocked_domains()
    analyze_blocked_domains(blocked_domains)
