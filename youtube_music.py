import time
import sys
import asyncio
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
start_timestamp = None
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

print(f"Rich Presence elindítva optimális időzítéssel...")

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
                start_timestamp = int(time.time())
                
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    start=start_timestamp
                )
                print(f"Frissítve: {current_track}")
            else:
                RPC.clear()
                print("Zene leállítva.")
                start_timestamp = None
            
            last_track = current_track
        except Exception:
            is_connected = False
            last_track = None
            start_timestamp = None
            
    # FELEMELTÜK 7 MÁSODPERCRE! Így nem akad ki a Discord hangcsatornája, 
    # és a szerver sem fogja megállítani az idődet.
    time.sleep(7)