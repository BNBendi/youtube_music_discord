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
start_timestamp = None  # Itt tároljuk, mikor kezdődött a szám

def connect_discord():
    global is_connected
    try:
        if not is_connected:
            RPC.connect()
            is_connected = True
            print("Sikeresen csatlakozva a Discordhoz!")
    except Exception:
        is_connected = False

# --- WINDOWS MÉDIA LEKÉRÉS + IDŐZÍTÉS ---
async def get_windows_media():
    try:
        manager = await SessionManager.request_async()
        current_session = manager.get_current_session()
        if current_session:
            source_app = current_session.source_app_user_model_id.lower()
            if "brave" in source_app or "chrome" in source_app:
                info = await current_session.try_get_media_properties_async()
                timeline = current_session.get_timeline_properties()
                
                if info.title:
                    # Kiszámoljuk, mikor kezdődött a szám a Windows pozíció alapján
                    # timeline.position megmondja, hány másodperce megy a szám
                    position_seconds = timeline.position.total_seconds()
                    calculated_start = int(time.time() - position_seconds)
                    
                    return f"{info.title} - {info.artist}", calculated_start
    except Exception:
        pass
    return None, None

# --- LINUX MÉDIA LEKÉRÉS + IDŐZÍTÉS ---
def get_linux_media():
    try:
        for uri in get_players_uri():
            if 'youtube' in uri or 'chromium' in uri or 'googleout' in uri or 'brave' in uri:
                player = Player(dbus_interface_info={'dbus_uri': uri})
                meta = player.Metadata
                title = meta.get('xesam:title', 'Ismeretlen szám')
                artist = ", ".join(meta.get('xesam:artist', ['Ismeretlen előadó']))
                
                # Linux alatt az mpris mikromásodpercben adja meg a pozíciót
                try:
                    position_seconds = player.Position / 1000000
                except:
                    position_seconds = 0
                calculated_start = int(time.time() - position_seconds)
                
                return f"{title} - {artist}", calculated_start
    except Exception:
        pass
    return None, None

print(f"Rich Presence elindítva ({sys.platform} módban, számlálóval)...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        current_track, track_start = asyncio.run(get_windows_media())
    else:
        current_track, track_start = get_linux_media()
    
    # Ha változott a zene, VAGY ha a számláló nagyon elcsúszott (pl. áttekertél a számban)
    if is_connected and (current_track != last_track or (track_start and start_timestamp and abs(track_start - start_timestamp) > 5)):
        try:
            if current_track:
                title, artist = current_track.split(" - ", 1)
                start_timestamp = track_start
                
                # Az `start=start_timestamp` paraméter indítja el a Discord számlálót!
                RPC.update(
                    details=f"🎵 {title}",
                    state=f"👤 {artist}",
                    large_image="yt_logo",
                    start=start_timestamp
                )
                print(f"Frissítve (számlálóval): {current_track}")
            else:
                RPC.clear()
                print("Zene leállítva, státusz törölve.")
                start_timestamp = None
            
            last_track = current_track
        except Exception:
            print("Discord kapcsolat megszakadt...")
            is_connected = False
            last_track = None
            start_timestamp = None
            
    time.sleep(3) # 3 másodpercre vettem le, hogy ha áttekersz a zenében, azonnal észrevegye és javítsa a számlálót!