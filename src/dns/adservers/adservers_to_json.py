import json


def adservers_to_json():
    result = {
        "A": {}
    }

    with open("input.txt", "r") as file:
        domains = file.read().splitlines()

        for domain in domains:
            if domain.strip():
                if not domain.endswith('.'):
                    domain += '.'

                result["A"][domain] = "0.0.0.0"

    with open("output.json", "w") as json_file:
        json.dump(result, json_file, indent=4)


if __name__ == "__main__":
    adservers_to_json()


