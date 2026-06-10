import time
import sys
import asyncio
from pypresence import Presence

# Automatikus rendszerfelismerés
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

# Univerzális belső stopper változói
start_time = 0
local_total_duration = 180 

def format_time(seconds):
    if seconds < 0:
        return "0:00"
    minutes = int(seconds) // 60
    secs = int(seconds) % 60
    return f"{minutes}:{secs:02d}"

def make_progress_bar(current, total, bar_length=14):
    fraction = current / total
    if fraction > 1.0:
        fraction = 1.0
        
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

def estimate_duration(title):
    """Okos időbecslő a szám címe alapján, hogy ne legyen minden zene 3 perc"""
    title_lower = title.lower()
    if "mix" in title_lower or "compilation" in title_lower or "set" in title_lower:
        return 600  # 10 perc a mixeknek
    if "slowed" in title_lower or "reverb" in title_lower:
        return 240  # 4 perc a lassított számoknak
    if "speed" in title_lower or "nightcore" in title_lower:
        return 140  # 2:20 a gyorsított számoknak
    return 195  # 3:15 egy átlagos modern zenének

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
                    return {
                        "track_info": f"{info.title} - {info.artist}",
                        "title": info.title,
                        "artist": info.artist
                    }
    except Exception:
        windows_manager = None
    return None

def get_linux_media():
    try:
        for uri in get_players_uri():
            if "brave" in uri.lower() or "chrome" in uri.lower():
                player = Player(dbus_interface_info={'dbus_uri': uri})
                metadata = player.Metadata
                title = metadata.get('xesam:title', '')
                artist_list = metadata.get('xesam:artist', [])
                artist = artist_list[0] if artist_list else 'Ismeretlen előadó'
                if title:
                    return {
                        "track_info": f"{title} - {artist}",
                        "title": title,
                        "artist": artist
                    }
    except Exception:
        pass
    return None

# Indítási üzenet a rendszer alapján
rendszer_nev = "Windows SMTC" if IS_WINDOWS else "Linux MPRIS2"
print(f"YouTube Music Rich Presence elindítva ({rendszer_nev} motor)...")

while True:
    connect_discord()
    
    # Adatok lekérése attól függően, hogy milyen rendszeren futunk
    if IS_WINDOWS:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        media_data = loop.run_until_complete(get_windows_media())
    else:
        media_data = get_linux_media()
        
    now = time.time()
    
    if media_data:
        # ÚJ SZÁM ÉSZLELÉSE (Mindkét rendszeren ugyanúgy működik)
        if media_data["track_info"] != last_track:
            start_time = now
            local_total_duration = estimate_duration(media_data["title"])
            last_track = media_data["track_info"]
            print(f"Most szól: {last_track} (Becsült hossz: {format_time(local_total_duration)})")
            
        # Sima számlálás másodpercenként
        elapsed = int(now - start_time)
        if elapsed > local_total_duration:
            elapsed = local_total_duration

        # Szöveges csík összerakása
        p_bar = make_progress_bar(elapsed, local_total_duration)
        time_text = f"[{format_time(elapsed)} / {format_time(local_total_duration)}]"
        
        if is_connected:
            try:
                # Mivel CSAK szöveget küldünk, start/end nélkül, Windows-on SE lesz zöld ikon!
                RPC.update(
                    details=f"🎵 {media_data['title']}",
                    state=f"{p_bar} {time_text}",
                    large_image="youtube_music_logo",
                    large_text=f"Előadó: {media_data['artist']}"
                )
            except Exception:
                is_connected = False
    else:
        if last_track is not None:
            try:
                RPC.clear()
            except Exception:
                pass
            print("Zene leállítva.")
            last_track = None
            
    time.sleep(1)