import time
import sys
import asyncio
from pypresence import Presence

# Megnézzük, milyen rendszeren futunk
IS_WINDOWS = sys.platform.startswith('win')

if IS_WINDOWS:
    # Windows-specifikus import
    from winsdk.windows.media.control import GlobalSystemMediaTransportControlsSessionManager as SessionManager
else:
    # Linux-specifikus importok
    from mpris2 import get_players_uri, Player

# A te Discord alkalmazás ID-d
client_id = '1512429120431194217' 

RPC = Presence(client_id)
is_connected = False

def connect_discord():
    global is_connected
    try:
        if not is_connected:
            RPC.connect()
            is_connected = True
            print("Sikeresen csatlakozva a Discordhoz!")
    except Exception:
        is_connected = False

# --- WINDOWS MÉDIA LEKÉRÉS ---
async def get_windows_media():
    try:
        manager = await SessionManager.request_async()
        current_session = manager.get_current_session()
        if current_session:
            source_app = current_session.source_app_user_model_id.lower()
            if "brave" in source_app or "chrome" in source_app:
                info = await current_session.try_get_media_properties_async()
                return info.title, info.artist
    except Exception:
        pass
    return None, None

# --- LINUX MÉDIA LEKÉRÉS ---
def get_linux_media():
    try:
        for uri in get_players_uri():
            if 'youtube' in uri or 'chromium' in uri or 'googleout' in uri or 'brave' in uri:
                player = Player(dbus_interface_info={'dbus_uri': uri})
                meta = player.Metadata
                title = meta.get('xesam:title', 'Ismeretlen szám')
                artist = ", ".join(meta.get('xesam:artist', ['Ismeretlen előadó']))
                return title, artist
    except Exception:
        pass
    return None, None

print(f"Rich Presence elindítva ({sys.platform} módban)...")

while True:
    connect_discord()
    
    # Rendszer alapján döntjük el, melyik függvényt hívjuk meg
    if IS_WINDOWS:
        title, artist = asyncio.run(get_windows_media())
    else:
        title, artist = get_linux_media()
    
    if is_connected:
        try:
            if title:
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    large_image="yt_logo"
                )
                print(f"Frissítve: {title} - {artist}")
            else:
                RPC.clear()
                print("Nem szól semmi a Brave-ben...")
        except Exception:
            print("Discord kapcsolat megszakadt, újrapróbálkozás...")
            is_connected = False
            
    time.sleep(15)