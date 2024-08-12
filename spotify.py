import os
import requests
from dotenv import load_dotenv


load_dotenv()

spotify_access_token= ""
spotifyClientID= os.getenv("spotify_client_id")
spotifyClientSecret= os.getenv("spotify_client_secret")

# Generates new Spotify Token
def generate_spotify_token():
    global spotify_access_token
    print("Fetching Spotify Access token...")
    
    url="https://accounts.spotify.com/api/token"
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {
        "grant_type": "client_credentials",
        "client_id": spotifyClientID,
        "client_secret": spotifyClientSecret
    }
    
    response= requests.post(url,headers=headers,data=data)
    
    if response.status_code == 200:
        token_info=response.json()
        spotify_access_token= token_info['access_token']
        print("Spotify Access Token fetched successfully.")
        return 1     
    else:
        print("Filed to fetch Spotify Access Token , Trying Again!")
        return ""
        
# Searches Artists by Name
def search_artists(*,artist_name:str):
    print("Searching Artists by Name...")
    
    url= "https://api.spotify.com/v1/search"
    
    params= {
        'q':artist_name,
        'type':"artist",
        'limit':5 #set the limit for artists
    }
    
    headers= {
        'Authorization': f"Bearer {spotify_access_token}"
    }
    
    response= requests.get(url,headers=headers,params=params)
    
    if response.status_code == 200:
        #update from here
        print(response.json())
    else:
        print("Failed to fetch Data!!")