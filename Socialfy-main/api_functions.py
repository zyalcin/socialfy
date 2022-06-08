import requests


CLIENT_ID = '2dec1cbc10ad413d900562729601f2b8'
CLIENT_SECRET = '76561d6d49a24ea69f3c6a0addd5148a'


AUTH_URL = 'https://accounts.spotify.com/api/token'

# POST
auth_response = requests.post(AUTH_URL, {
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
})

# convert the response to JSON
auth_response_data = auth_response.json()

# save the access token
access_token = auth_response_data['access_token']


headers = {
    'Authorization': 'Bearer {token}'.format(token=access_token)
}

# base URL of all Spotify API endpoints
BASE_URL = 'https://api.spotify.com/v1/'

# Track ID from the URI
#track_id = '4A5FLaZI3Ni5eT0c9fqi8F'


# actual GET request with proper header
def get_track_image_url(track_id):
    try:
        print(track_id)
        r = requests.get(BASE_URL + track_id, headers=headers)
        r = r.json()
        #print(r)
        name = r.get('name')
        url = r.get('album').get('images')[0].get('url')
        print(url)
        return name, url
    except Exception as e:
        print(e)
        return str(e), ""

def get_episode_image_url(track_id):
    try:
        print("URL with the show id is {}".format(track_id))
        print(BASE_URL + track_id)
        r = requests.get(BASE_URL + track_id + "?market=US", headers=headers)
        r = r.json()
        #print("RESPONSE: {}".format(r))
        name = r.get('name')
        url = r.get('images')[0].get('url')
        #print(url)
        return name, url
    except Exception as e:
        print("EXCEPTION")
        print(e)
        return str(e), ""

def get_show_image_url(track_id):
    try:
        print("in show image")
        print("URL with the show id is {}".format(track_id))
        print(BASE_URL + track_id)
        r = requests.get(BASE_URL + track_id + "?market=US", headers=headers)
        r = r.json()
        #print("RESPONSE: {}".format(r))
        name = r.get('name')
        url = r.get('images')[0].get('url')
        #print(url)
        return name, url
    except Exception as e:
        print("EXCEPTION")
        print(e)
        return str(e), ""

def get_playlist_image_url(track_id):
    try:
        r = requests.get(BASE_URL + track_id, headers=headers)
        r = r.json()
        #print("RESPONSE: {}".format(r))
        name = r.get('name')
        url = r.get('images')[0].get('url')
        #print(url)
        return name, url
    except Exception as e:
        print("EXCEPTION")
        print(e)
        return str(e), ""