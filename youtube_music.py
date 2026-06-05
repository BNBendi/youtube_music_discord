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
last_track = None  # Itt jegyezzük meg, mi szólt legutóbb

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
    try:
        manager = await SessionManager.request_async()
        current_session = manager.get_current_session()
        if current_session:
            source_app = current_session.source_app_user_model_id.lower()
            if "brave" in source_app or "chrome" in source_app:
                info = await current_session.try_get_media_properties_async()
                if info.title:
                    return f"{info.title} - {info.artist}"
    except Exception:
        pass
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

print(f"Rich Presence elindítva ({sys.platform} módban)...")

while True:
    connect_discord()
    
    # Lekérjük az aktuális zenét
    if IS_WINDOWS:
        current_track = asyncio.run(get_windows_media())
    else:
        current_track = get_linux_media()
    
    # CSAK AKKOR NYÚLUNK A DISCORDHOZ, HA VÁLTOZÁS TÖRTÉNT!
    if is_connected and current_track != last_track:
        try:
            if current_track:
                # Szétválasztjuk a címet és az előadót a megjelenítéshez
                title, artist = current_track.split(" - ", 1)
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    large_image="yt_logo"
                )
                print(f"Discord státusz frissítve: {current_track}")
            else:
                RPC.clear()
                print("Zene leállítva, Discord státusz törölve.")
            
            last_track = current_track  # Elmentjük az új állapotot
        except Exception:
            print("Discord kapcsolat megszakadt...")
            is_connected = False
            last_track = None
            
    time.sleep(5) # Levehetjük 5 másodpercre, mert az új logika nem spammeli a Discordot