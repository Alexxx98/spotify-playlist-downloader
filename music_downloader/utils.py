import requests


def get_playlist(url, token):
    header = {"Authorization": "Bearer " + token}
    response = requests.get(url, headers=header)
    data = response.json()
    return data