import os
import spotipy
import yt_dlp
import shutil

from flask import Flask, session, request, url_for, render_template, redirect, send_file
from spotipy.oauth2 import SpotifyOAuth
from spotipy.cache_handler import FlaskSessionCacheHandler
from googleapiclient.discovery import build
from werkzeug.middleware.proxy_fix import ProxyFix
from dotenv import load_dotenv
from urllib.parse import quote
from utils import get_playlist


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.wsgi_app = ProxyFix(
    app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1
)

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')
redirefct_uri = 'http://192.168.1.12:82/callback'
scopes = 'user-library-read playlist-read-private playlist-read-collaborative'

cache_handler = FlaskSessionCacheHandler(session)

sp_oauth = SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirefct_uri,
    scope=scopes,
    cache_handler=cache_handler,
    show_dialog=True,
)
sp = spotipy.Spotify(auth_manager=sp_oauth)

@app.route('/')
def connect():
    return render_template('connect.html')


@app.route('/login')
def login():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    return redirect(url_for('home'))


@app.route('/callback')
def callback():
    sp_oauth.get_access_token(request.args['code'])
    return redirect(url_for('home'))


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('connect'))


@app.route('/home')
def home():
    if not sp_oauth.validate_token(cache_handler.get_cached_token()):
        auth_url = sp_oauth.get_authorize_url()
        return redirect(auth_url)
    
    playlists = sp.current_user_playlists()['items']

    return render_template('home.html', playlists=playlists)


@app.route('/playlist/<playlist_id>')
def playlist(playlist_id):
    token = cache_handler.get_cached_token()['access_token']
    playlists = sp.current_user_playlists()['items']

    for playlist in playlists:
        if playlist['id'] == playlist_id:
            playlist_url = playlist['tracks']['href']
            playlist_details = get_playlist(playlist_url, token)['items']
            return render_template(
                'playlist.html',
                playlist=playlist,
                playlist_details=playlist_details,
            )
        
    return redirect(url_for('home', playlists=playlists))


@app.route('/download/<artist><track>')
def download(artist, track):
    youtube = build('youtube', 'v3', developerKey=os.getenv('GOOGLE_API_KEY'))
    
    # Generate the YT query
    request = youtube.search().list(
        part='snippet',
        maxResults=1,
        q=f'{artist} {track}'
    )

    # Get the video url
    response = request.execute()
    video_id = response['items'][0]['id']['videoId']
    video_url = f'https://www.youtube.com/watch?v={video_id}'

    # Create the Music folder on server side if does not exist
    music_directory = os.path.join(os.getcwd(), 'Music')
    try:
        os.mkdir(music_directory)
    except FileExistsError:
        pass

    # Setting options for the audio to download
    download_data = {
        'final_ext': 'wav',
        'format': 'bestaudio/best',
        'postprocessors': [{'key': 'FFmpegExtractAudio',
                            'nopostoverwrites': False,
                            'preferredcodec': 'wav',
                            'preferredquality': '320'}],
        'outtmpl': os.path.join(music_directory, '%(title)s.%(ext)s'),
        'ffmpeg_location': '/usr/bin/ffmpeg',
        }
    
    with yt_dlp.YoutubeDL(download_data) as ydl:
        ydl.download([video_url])

    # Get the song path
    song = os.listdir(music_directory)[0]
    song_path = os.path.join(music_directory, song)

    # Send response to the client side
    quoted_song = quote(song)
    response = send_file(song_path, as_attachment=True)
    response.headers['Content-Disposition'] = f'attachment; filename="{quoted_song}"'

    # Remove the song from server
    shutil.rmtree(music_directory)

    return response
