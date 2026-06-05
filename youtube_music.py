import time
import sys
import asyncio
import requests
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

# --- ALBUM BORÍTÓ KERESŐ API ---
def get_album_art_url(title, artist):
    try:
        # Tisztítjuk a keresési kifejezést a biztosabb találatért
        query = f"{artist} {title}".replace(" - Topic", "").replace("(Official Video)", "")
        url = f"https://itunes.apple.com/search?term={query}&entity=song&limit=1"
        
        response = requests.get(url, timeout=3).json()
        if response.get("resultCount", 0) > 0:
            # Megvan a kép! Alapból kis képet ad, de átírjuk 600x600-as felbontásra, hogy szép legyen
            artwork_url = response["results"][0]["artworkUrl100"]
            high_res_url = artwork_url.replace("100x100bb.jpg", "600x600bb.jpg")
            return high_res_url
    except Exception:
        pass
    return "yt_logo"  # Ha hibára fut vagy nincs találat, az alapértelmezett képedet használja

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

print(f"Rich Presence elindítva borítókép-keresővel...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        current_track = asyncio.run(get_windows_media())
    else:
        current_track = get_linux_media()
    
    if is_connected and current_track != last_track:
        try:
            if current_track:
                title, artist = current_track.split(" - ", 1)
                
                # Tisztítás és borítókép lekérése az API-ból
                print(f"Borítókép keresése a neten: {title}...")
                cover_image_url = get_album_art_url(title, artist)
                
                RPC.clear()
                time.sleep(0.2)
                
                clean_timestamp = int(time.time())
                
                # Beküldjük a Discordnak a közvetlen kép-linket (large_image lehet URL is!)
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    start=clean_timestamp,
                    large_image=cover_image_url,
                    large_text=f"Album: {title}"
                )
                print(f"Sikeresen frissítve borítóval: {current_track}")
            else:
                RPC.clear()
                print("Zene leállítva.")
            
            last_track = current_track
        except Exception as e:
            print(f"Discord hiba: {e}")
            is_connected = False
            last_track = None
            
    time.sleep(5)