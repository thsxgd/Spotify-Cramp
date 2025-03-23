import spotipy
import time
import os
import json
from spotipy.oauth2 import SpotifyOAuth
from datetime import datetime, timedelta


# You need to create an app in the Spotify Developer Dashboard:
# https://developer.spotify.com/dashboard/applications
# Replace the values with your data
os.environ["SPOTIPY_CLIENT_ID"] = "insert your data here"
os.environ["SPOTIPY_CLIENT_SECRET"] = "insert your data here"
os.environ["SPOTIPY_REDIRECT_URI"] = "http://localhost:8888/callback"


scope = "user-read-currently-playing user-read-playback-state"

def setup_spotify_client():
    """Set up and return an authenticated Spotify client."""
    sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    return sp

def format_time(ms):
    """Convert milliseconds to a readable time format."""
    return str(timedelta(milliseconds=ms)).split('.')[0]

def get_current_track_info(sp):
    """Get information about the currently playing track."""
    try:
        
        current_playback = sp.current_playback()
        
        if current_playback is None or not current_playback['is_playing']:
            return "No track currently playing."
        
        
        track = current_playback['item']
        track_name = track['name']
        artists = ", ".join([artist['name'] for artist in track['artists']])
        album_name = track['album']['name']
        
        
        duration_ms = track['duration_ms']
        progress_ms = current_playback['progress_ms']
        
        remaining_ms = duration_ms - progress_ms
        
        
        playlist_name = "Unknown playlist"
        context = current_playback.get('context')
        
        if context and context['type'] == 'playlist':
            
            playlist_id = context['uri'].split(':')[-1]
            try:
                playlist = sp.playlist(playlist_id)
                playlist_name = playlist['name']
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 404:
                    playlist_name = "Private or unavailable playlist"
                else:
                    playlist_name = f"Error retrieving playlist: {e.msg}"
            except Exception:
                playlist_name = "Error retrieving playlist info"
        
        
        output = f"""
{'=' * 50}
Currently Playing: {track_name}
Artist: {artists}
Album: {album_name}
Playlist: {playlist_name}
Progress: {format_time(progress_ms)} / {format_time(duration_ms)}
Remaining: {format_time(remaining_ms)}
{'=' * 50}
"""
        return output
    
    except Exception as e:
        return f"Error getting track info: {str(e)}"

def save_track_data(track_data, duration_listened):
    """Save track data to a text file."""
    filename = "spotify_history.txt"
    
    try:
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        
        mins, secs = divmod(duration_listened, 60)
        duration_str = f"{int(mins)}:{int(secs):02d}"
        
      
        track_name = track_data.get('name', 'Unknown')
        artist_names = ", ".join([artist['name'] for artist in track_data.get('artists', [])])
        album_name = track_data.get('album', {}).get('name', 'Unknown')
        album_release = track_data.get('album', {}).get('release_date', 'Unknown')
        track_duration = format_time(track_data.get('duration_ms', 0))
        popularity = track_data.get('popularity', 'Unknown')
        track_uri = track_data.get('uri', 'Unknown')
        explicit = "Yes" if track_data.get('explicit', False) else "No"
        
        
        line = (f"[{timestamp}] Track: {track_name} | Artists: {artist_names} | "
                f"Album: {album_name} ({album_release}) | Duration: {track_duration} | "
                f"Listened for: {duration_str} | Popularity: {popularity} | "
                f"Explicit: {explicit} | URI: {track_uri}\n")
        
        # Write to file
        with open(filename, 'a', encoding='utf-8') as f:
            f.write(line)
            
        print(f"Track data saved to {filename}")
    except Exception as e:
        print(f"Error saving track data: {str(e)}")

def main():
    """Main function to run the Spotify bot."""
    print("Initializing Spotify Bot...")
    sp = setup_spotify_client()
    
    print("Spotify Bot is now running. Press Ctrl+C to exit.")
    print(f"Track history will be saved to spotify_history.txt")
    
    
    last_track_id = None
    last_is_playing = False
    track_start_time = None
    current_track_data = None
    
    try:
        while True:
            
            current_playback = sp.current_playback()
            
            refresh_needed = False
            
            if current_playback is None:
                
                current_track_id = None
                current_is_playing = False
                
                
                if last_is_playing and last_track_id and track_start_time:
                    duration_listened = time.time() - track_start_time
                    save_track_data(current_track_data, duration_listened)
                    track_start_time = None
                    current_track_data = None
                
                if last_is_playing: 
                    refresh_needed = True
            else:
                current_is_playing = current_playback['is_playing']
                
                if current_is_playing:
                    current_track_id = current_playback['item']['id']
                    
                    
                    if current_track_id != last_track_id and last_track_id and track_start_time:
                        duration_listened = time.time() - track_start_time
                        save_track_data(current_track_data, duration_listened)
                    
                    
                    if current_track_id != last_track_id or not last_is_playing:
                        track_start_time = time.time()
                        current_track_data = current_playback['item']
                        refresh_needed = True
                else:
                    
                    if last_is_playing and last_track_id and track_start_time:
                        duration_listened = time.time() - track_start_time
                        save_track_data(current_track_data, duration_listened)
                        track_start_time = None
                    
                    current_track_id = None
                    
                    if last_is_playing:
                        refresh_needed = True
            
            
            last_track_id = current_track_id
            last_is_playing = current_is_playing
            
            if refresh_needed:
                
                os.system('cls' if os.name == 'nt' else 'clear')
                track_info = get_current_track_info(sp)
                print(track_info)
                print("Detected track change or playback state change. Refreshed display.")
            else:
               
                time.sleep(1) 
                
                
                if int(time.time()) % 30 == 0:
                    os.system('cls' if os.name == 'nt' else 'clear')
                    track_info = get_current_track_info(sp)
                    print(track_info)
    
    except KeyboardInterrupt:
        
        if last_is_playing and last_track_id and track_start_time:
            duration_listened = time.time() - track_start_time
            save_track_data(current_track_data, duration_listened)
        
        print("\nSpotify Bot stopped.")

if __name__ == "__main__":
    main()