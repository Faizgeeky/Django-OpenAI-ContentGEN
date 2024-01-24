import requests

def get_weather(location):
    # city = "Hanoi"
    url = f"http://wttr.in/{location}?format=3"

    response = requests.get(url)
    return response.text
    