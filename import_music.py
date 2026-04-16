import re
import time
import argparse
from yandex_music import Client


def parse_vk_music_file(filepath):
    tracks = []
    current_track_lines = []
    # Regex to match duration e.g. 3:44 or 10:22 or 0:45
    duration_pattern = re.compile(r'^\d{1,2}:\d{2}$')
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            if duration_pattern.match(line):
                if current_track_lines:
                    # Combine all lines before the duration into a single search query
                    query = " ".join(current_track_lines)
                    tracks.append(query)
                    current_track_lines = []
            else:
                current_track_lines.append(line)
                
    # Handle the case where the file might not end with a duration line
    if current_track_lines:
        query = " ".join(current_track_lines)
        tracks.append(query)

    # Сначала добавляются старые треки (с конца списка), чтобы новые оказались наверху в Яндекс.Музыке
    tracks.reverse()
    return tracks

def main():
    parser = argparse.ArgumentParser(description='Import VK music to Yandex Music')
    parser.add_argument('file', help='Path to the txt file with VK music list')
    parser.add_argument('--token', required=True, help='Yandex Music API token')
    args = parser.parse_args()

    print("Parsing music file...")
    try:
        tracks = parse_vk_music_file(args.file)
        print(f"Found {len(tracks)} tracks to import.")
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    print("Authenticating in Yandex Music...")
    try:
        client = Client(args.token).init()
        me = client.me
        print(f"Successfully authenticated as {me.account.uid}")
    except Exception as e:
        print(f"Authentication failed: {e}")
        print("Please ensure your token is correct and valid.")
        return

    failed_tracks = []
    
    for i, query in enumerate(tracks):
        print(f"[{i+1}/{len(tracks)}] Searching for: '{query}'...")
        try:
            search_result = client.search(text=query, type_='track')
            if search_result and search_result.tracks and search_result.tracks.results:
                track = search_result.tracks.results[0]
                artists = ", ".join([a.name for a in track.artists])
                title = track.title
                print(f"  -> Found: {artists} - {title}")
                
                # Add to liked tracks (using the client method)
                try:
                     client.users_likes_tracks_add([track.id])
                     print(f"  -> Added to Liked Tracks.")
                except Exception as e:
                     print(f"  -> Could not add to liked tracks: {e}")
                     failed_tracks.append(query)
            else:
                print(f"  -> Not found on Yandex Music.")
                failed_tracks.append(query)
                
        except Exception as e:
            print(f"  -> Error: {e}")
            failed_tracks.append(query)
            
        # Sleep slightly to avoid spamming the Yandex Music API
        time.sleep(1)
        
    if failed_tracks:
        print(f"\nCompleted! However, {len(failed_tracks)} tracks were not found or failed to add.")
        
        with open('failed_tracks.txt', 'w', encoding='utf-8') as f:
            for t in failed_tracks:
                f.write(t + "\n")
        print("Failed tracks saved to failed_tracks.txt")
    else:
        print("\nAll tracks successfully imported!")

if __name__ == '__main__':
    main()
