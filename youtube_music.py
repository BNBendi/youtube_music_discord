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
                    track_data = {
                        "track_info": f"{info.title} - {info.artist}",
                        "title": info.title,
                        "artist": info.artist,
                        "total_duration": 0,
                        "current_position": 0
                    }
                    
                    try:
                        timeline = current_session.get_timeline_properties()
                        if timeline:
                            # ÁTVÁLTÁS: A Windows belső Ticks értékét (100-nanoszekundum) másodperccé alakítjuk (/ 10.000.000)
                            # Ha a Winsdk közvetlenül engedi a .total_seconds()-et, akkor azt használjuk, ha nem, a belső duration-t
                            try:
                                track_data["total_duration"] = int(timeline.end_position.total_seconds())
                                track_data["current_position"] = int(timeline.position.total_seconds())
                            except AttributeError:
                                track_data["total_duration"] = int(timeline.end_position.duration / 10000000)
                                track_data["current_position"] = int(timeline.position.duration / 10000000)
                    except Exception:
                        pass
                        
                    return track_data
    except Exception:
        windows_manager = None
    return None

print("YouTube Music Rich Presence elindítva (Javított másodperc-alapú kijelzéssel)...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        media_data = asyncio.run(get_windows_media())
    else:
        media_data = None
    
    if media_data:
        current_track = media_data["track_info"]
        
        if is_connected and current_track != last_track:
            try:
                now = int(time.time())
                start_timestamp = now
                end_timestamp = None
                
                # Csak akkor számolunk csíkot, ha értelmes hosszt kaptunk vissza
                if media_data["total_duration"] > 0:
                    start_timestamp = now - media_data["current_position"]
                    end_timestamp = start_timestamp + media_data["total_duration"]
                
                RPC.clear()
                time.sleep(0.2)
                
                RPC.update(
                    details=f"🎵 {media_data['title']}",
                    state=f"👤 {media_data['artist']}",
                    start=start_timestamp,
                    end=end_timestamp,
                    large_image="youtube_music_logo",
                    large_text="YouTube Music"
                )
                print(f"Frissítve a Discordon: {current_track} ({media_data['total_duration']} mp)")
                last_track = current_track
                
            except Exception as e:
                print(f"Discord hiba az update-nél: {e}")
                is_connected = False
                last_track = None
    else:
        if last_track is not None:
            try:
                RPC.clear()
            except Exception:
                pass
            print("Zene leállítva.")
            last_track = None
            
    time.sleep(3)