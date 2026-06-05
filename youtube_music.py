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

# --- FELOKOSÍTOTT WINDOWS MÉDIA LEKÉRDEZÉS ---
async def get_windows_media():
    global windows_manager
    try:
        if windows_manager is None:
            windows_manager = await SessionManager.request_async()
        current_session = windows_manager.get_current_session()
        if current_session:
            source_app = current_session.source_app_user_model_id.lower()
            if "brave" in source_app or "chrome" in source_app:
                
                # 1. Lekérjük a címet és az előadót
                info = await current_session.try_get_media_properties_async()
                
                # 2. Lekérjük a szám hosszát és pozícióját (Timeline)
                timeline = current_session.get_timeline_properties()
                
                if info.title:
                    # Kiszámoljuk másodpercben a teljes hosszt és hogy hol tart a zene
                    total_seconds = timeline.end_position.total_seconds()
                    position_seconds = timeline.position.total_seconds()
                    
                    return {
                        "track_info": f"{info.title} - {info.artist}",
                        "title": info.title,
                        "artist": info.artist,
                        "total_duration": total_seconds,
                        "current_position": position_seconds
                    }
    except Exception as e:
        windows_manager = None
    return None

print("YouTube Music Rich Presence elindítva (Szám hossza kijelzéssel)...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        media_data = asyncio.run(get_windows_media())
    else:
        media_data = None # Linuxon bonyolultabb, most a Windowsra fókuszálunk
    
    if media_data:
        current_track = media_data["track_info"]
        
        # Ha új szám kezdődött, vagy a felhasználó beletekert a zenébe
        if is_connected and current_track != last_track:
            try:
                now = int(time.time())
                
                # KISZÁMOLJUK A DISCORDNAK A START ÉS END IDŐKET:
                # A start idő az, amikor a szám ELINDULT a valóságban (mostani idő mínusz ahol épp tart a zene)
                start_timestamp = now - int(media_data["current_position"])
                # A vég idő pedig a start idő plusz a szám teljes hossza
                end_timestamp = start_timestamp + int(media_data["total_duration"])
                
                RPC.clear()
                time.sleep(0.2)
                
                # Küldés a Discordnak a pontos számdurációval!
                RPC.update(
                    details=f"🎵 {media_data['title']}",
                    state=f"👤 {media_data['artist']}",
                    start=start_timestamp,  # Mikor indult a szám
                    end=end_timestamp,      # Mikor jár le a szám
                    large_image="youtube_music_logo",
                    large_text="YouTube Music"
                )
                print(f"Frissítve a szám hosszával: {current_track}")
                last_track = current_track
                
            except Exception as e:
                print(f"Discord hiba: {e}")
                is_connected = False
                last_track = None
    else:
        if last_track is not None:
            RPC.clear()
            print("Zene leállítva.")
            last_track = None
            
    time.sleep(2) # Sűrűbben ellenőrizzük (2 mp), hogy ha belatekered a zenébe, lekövesse