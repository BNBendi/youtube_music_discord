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

# Belső motor változói a fagyás ellen
local_current_position = 0
local_total_duration = 0
last_update_time = 0

def format_time(seconds):
    if seconds is None or seconds < 0:
        return "0:00"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"

def make_progress_bar(current, total, bar_length=14):
    if not total or total <= 0:
        return "🔘" + "▬" * (bar_length - 1)
    
    fraction = current / total
    dot_position = int(fraction * bar_length)
    if dot_position >= bar_length:
        dot_position = bar_length - 1
        
    bar = ""
    for i in range(bar_length):
        if i == dot_position:
            bar += "🔘"
        else:
            bar += "▬"
            
    return bar

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

print("YouTube Music Rich Presence elindítva (Kényszerített szinkronizáció)...")

while True:
    connect_discord()
    
    if IS_WINDOWS:
        media_data = asyncio.run(get_windows_media())
    else:
        media_data = None
    
    now = time.time()
    
    if media_data:
        if media_data["track_info"] != last_track:
            local_current_position = media_data["current_position"]
            local_total_duration = media_data["total_duration"]
            last_update_time = now
            last_track = media_data["track_info"]
            print(f"Új zeneszám: {last_track}")
        else:
            time_passed = now - last_update_time
            expected_pos = local_current_position + time_passed
            
            if abs(media_data["current_position"] - expected_pos) > 4:
                local_current_position = media_data["current_position"]
                last_update_time = now
            else:
                local_current_position = expected_pos
                last_update_time = now
                
            if local_total_duration > 0 and local_current_position > local_total_duration:
                local_current_position = local_total_duration

        # Sáv és idő formázása
        p_bar = make_progress_bar(local_current_position, local_total_duration)
        time_text = f"[{format_time(local_current_position)} / {format_time(local_total_duration)}]"
        
        if is_connected:
            try:
                # MEZŐCSERE: A csík megy legfelülre, így kitörli a zöld órát!
                RPC.update(
                    details=f"{p_bar} {time_text}",
                    state=f"🎵 {media_data['title']} - {media_data['artist']}",
                    large_image="youtube_music_logo",
                    large_text="YouTube Music"
                )
            except Exception as e:
                print(f"Discord hiba: {e}")
                is_connected = False
    else:
        if last_track is not None:
            try:
                RPC.clear()
            except Exception:
                pass
            print("Zene leállítva.")
            last_track = None
            local_current_position = 0
            local_total_duration = 0
            
    time.sleep(1)