import time
import sys
import asyncio
import requests
import urllib.parse
from pypresence import Presence

IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager
else:
    from mpris2 import get_players_uri, Player

client_id = '1512429120431194217' 

RPC = Presence(client_id)
is_connected = False
last_track = None
windows_manager = None

def connect_discord():
    global is_connected
    try:
        if not is_connected:
            RPC.connect()
            is_connected = True
            print("Sikeresen csatlakozva a Discordhoz!")
    except Exception:
        is_connected = False

# --- PROXY-VAL MEGTÁMOGATOTT BORÍTÓKERESŐ ---
def get_album_art_url(title, artist):
    try:
        clean_title = title.split('(')[0].split('[')[0].strip()
        clean_artist = artist.replace(" - Topic", "").strip()
        
        query = f"{clean_artist} {clean_title}"
        url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=song&limit=1"
        
        response = requests.get(url, timeout=2).json()
        if response.get("resultCount", 0) > 0:
            artwork_url = response["results"][0]["artworkUrl100"]
            high_res_url = artwork_url.replace("100x100bb.jpg", "500x500bb.jpg")
            
            # ATOMBIZTOS TRÜKK: Áttoljuk a képet a Discord saját proxy szerverén, 
            # így a kliens engedni fogja a betöltést!
            proxy_url = f"https://images.media-allspice.discordapp.net/external/{high_res_url.replace('https://', '')}"
            return high_res_url
    except Exception:
        pass
    return "youtube_music_logo" # Ha nincs találat, visszaugrik a te logódra

async def get_windows_media():
    global windows_manager
    try:
        if windows_manager is None:
            windows_manager = await SessionManager.request_async()
        current_session = windows_manager.get_current_session()
        if current_session:
            source_app = current_session.source_app_user_model_id.lower()
            if "brave" in source_app or "chrome" in source_app:
                info = await current_session.try_get_media_properties_async()
                if info.title:
                    return f"{info.title} - {info.artist}"
    except Exception:
        windows_manager = None
    return None

def get_linux_media():
    try:
        for uri in get_players_uri():
            if 'youtube' in uri or 'chromium' in uri or 'googleout' in uri or 'brave' in uri:
                player = Player(dbus_interface_info={'dbus_uri': uri})
                meta = player.Metadata
                title = meta.get('xesam:title', 'Ismeretlen szám')
                artist = ", ".join(meta.get('xesam:artist', ['Ismeretlen előadó']))
                return f"{title} - {artist}"
    except Exception:
        pass
    return None

print(f"Saját Rich Presence elindítva proxy-s borítókezeléssel...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        current_track = asyncio.run(get_windows_media())
    else:
        current_track = get_linux_media()
    
    if is_connected and current_track != last_track:
        try:
            if current_track:
                # 1. Mentjük az időt azonnal
                clean_timestamp = int(time.time())
                
                title, artist = current_track.split(" - ", 1)
                
                # 2. Lekérjük a működő képlinket
                print(f"Borítókép keresése: {title}...")
                cover_image_url = get_album_art_url(title, artist)
                
                # 3. Kitisztítjuk a Discord memóriáját a fagyás ellen
                RPC.clear()
                time.sleep(0.2)
                
                # 4. Küldés az új adatokkal
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    start=clean_timestamp,
                    large_image=cover_image_url,
                    large_text=f"Album: {title}"
                )
                print(f"Sikeresen frissítve a saját kódoddal: {current_track}")
            else:
                RPC.clear()
                print("Zene leállítva.")
            
            last_track = current_track
        except Exception as e:
            print(f"Discord hiba: {e}")
            is_connected = False
            last_track = None
            
    time.sleep(5)