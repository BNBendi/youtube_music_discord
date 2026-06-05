import time
from pypresence import Presence
from mpris2 import get_players_uri, Player

# A Discord Developer Portalon létrehozott alkalmazásod ID-ja
client_id = '1512429120431194217' 
RPC = Presence(client_id)
RPC.connect()

print("Discord Rich Presence elindítva...")

def get_yotube_music_info():
    # Megkeressük a futó YouTube Music lejátszót a Linuxban
    for uri in get_players_uri():
        if 'googleout' in uri or 'youtube' in uri or 'chromium' in uri or 'brave' in uri:
            player = Player(dbus_interface_info={'dbus_uri': uri})
            meta = player.Metadata
            
            # Cím és előadó kiszedése
            title = meta.get('xesam:title', 'Ismeretlen szám')
            artist = ", ".join(meta.get('xesam:artist', ['Ismeretlen előadó']))
            return title, artist
    return None, None

while True:
    try:
        title, artist = get_yotube_music_info()
        if title:
            RPC.update(
                details=f"🎵 {title}",
                state=f"👤 {artist}",
                large_image="youtube_music_logo" # Ha töltöttél fel logót Discordra
            )
        else:
            RPC.clear() # Ha nem szól semmi, eltünteti a státuszt
    except Exception as e:
        print(f"Hiba: {e}")
        
    time.sleep(15) # 15 másodpercenként frissít (a Discord limitje miatt)