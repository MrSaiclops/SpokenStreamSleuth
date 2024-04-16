from plexapi.server import PlexServer
from plexapi.media import SubtitleStream
from datetime import datetime
import os
import subprocess
import requests
from iso639 import Lang
import traceback

# ANSI escape codes for colors
WHITE = '\033[97m'
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

def read_config():
    config = {}
    with open("config.txt", "r") as file:
        for line in file:
            key, value = line.strip().split("=")
            config[key.strip()] = value.strip()
    return config
# Log file 
identifier_log = "./identifier.txt"

# Function to start logging for the run
def start_logging_run():
    with open(identifier_log, "a") as log_file:
        log_file.write("=" * 50 + "\n")
        log_file.write(f"Run started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write("=" * 50 + "\n")

# Function to finish logging for the run
def finish_logging_run(start_time):
    end_time = datetime.now()
    total_runtime = (end_time - start_time).total_seconds()
    with open(identifier_log, "a") as log_file:
        log_file.write("=" * 50 + "\n")
        log_file.write(f"Run completed at {end_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        log_file.write(f"Total runtime: {total_runtime:.2f} seconds\n")
        log_file.write("=" * 50 + "\n\n")

# Function to log file processing information
def log_file_processing(humanName, status, details=""):
    with open(identifier_log, "a") as log_file:
        log_file.write(f"{humanName} {status}")
        if details:
            log_file.write(f" {details}")
        log_file.write("\n")

# Start logging for the run
start_time = datetime.now()
start_logging_run()

def report_error(error_message):
    traceback_info = traceback.format_exc()

    print("\n--- ERROR ---")
    print(error_message)
    print("-" * 50)
    print(traceback_info)
    print("-" * 50)

filters = {
    'and': [
        {'episode.audioLanguage!': 'kor'},
        {'episode.audioLanguage!': 'ja-JP'},
        {'episode.audioLanguage!': 'en'},
        {'episode.audioLanguage!': 'en-US'},
        {'episode.audioLanguage!': 'deu'},
        {'episode.audioLanguage!': 'fra'},
        {'episode.audioLanguage!': 'spa'},
        {'episode.audioLanguage!': 'deu'},
        {'episode.audioLanguage!': 'ita'},
        {'episode.audioLanguage!': 'swe'},
        {'episode.audioLanguage!': 'ton'},
        {'episode.audioLanguage!': 'ja'}
    ]       
}

def translate_language_code(language_code):
    try:
        lang = Lang(language_code)
        return lang.pt2t  # ISO 639-2/T code
    except Exception as e:
        print(f"{RED}Error translating language code: {e}{RESET}")
        return None

def trim_video(input_file, output_file, duration, humanName):
    print(f"{CYAN}Trimming {humanName} to a 30-second audio clip...{RESET}")
    # Run FFmpeg command to trim the middle-most 30 seconds of the video and export as MP3
    subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-i', input_file, '-ss', '00:00:30', '-t', duration, '-vn', '-acodec', 'libmp3lame', output_file])
    print(f"{WHITE}Trimmed audio clip saved as an .mp3{RESET}")

def detect_language(audio_file_path, endpoint):
    print(f"{CYAN}Sending audio clip to Whisper for language detection...{RESET}")
    url = f"http://{endpoint}/detect-language"
    files = {'audio_file': open(audio_file_path, 'rb')}
    response = requests.post(url, files=files)

    if response.status_code == 200:
        data = response.json()
        detected_language = data.get('detected_language')
        language_code = data.get('language_code')
        print(f"{GREEN}Language detected: {BOLD}{detected_language} (ISO 639-1: {language_code}){RESET}")
        return language_code
    else:
        print(f"{RED}Error: {response.status_code}, {response.text}{RESET}")
        return None

def update_language_metadata(input_file, output_file, language_code, humanName):
    print(f"{CYAN}Updating language metadata for {humanName}...{RESET}")
    try:
        iso_language_code = translate_language_code(language_code)
        if iso_language_code:
            subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'warning', '-stats', '-i', input_file, '-map', '0', '-c', 'copy', f'-metadata:s:a:0', f'language={iso_language_code}', output_file])
            print(f"{GREEN}Language metadata updated successfully.{RESET}")
        else:
            print(f"{RED}Failed to translate language code.{RESET}")
    except Exception as e:
        print(f"{RED}Error updating language metadata: {e}{RESET}")

def update_language_metadata_mkv(input_file, language_code, humanName):
    print(f"{CYAN}Updating language metadata for MKV file: {humanName}...{RESET}")
    try:
        # Construct the mkvpropedit command with proper handling of file paths
        command = f'mkvpropedit "{input_file}" --edit track:a1 --set language={language_code}'
        
        # Execute the command
        subprocess.run(command, shell=True, check=True)
        
        print(f"{GREEN}Language metadata updated successfully for MKV file: {humanName}{RESET}")
    except Exception as e:
        print(f"{RED}Error updating language metadata for MKV file: {humanName}: {e}{RESET}")

def main():
    try:
        # Read configuration
        config = read_config()
        baseurl = config.get('plexURL')
        token = config.get('token')
        library = config.get('library')
        endpoint = config.get('whisper')

        #Create PlexAPI string
        plex = PlexServer(baseurl, token)
        shows = plex.library.section(library)

        for episode in shows.searchEpisodes(filters=filters):
            audio_stream = episode.audioStreams()
            for stream in audio_stream:
                if stream is not None and (stream.languageCode is None or stream.languageCode == '' or stream.languageCode == 'unknown'):
                    part = episode.media[0].parts[0]
                    path = part.file
                    show = episode.grandparentTitle
                    partsid = part.id
                    humanName = f"{show} S{episode.seasonNumber}E{episode.index}"
                    # Episode Name: episode.title
                    # Show: show
                    # Season #: episode.seasonNumber
                    # Episode #: episode.index
                    print(f"{WHITE}Processing file: {humanName}{RESET}")

                    filename, extension = os.path.splitext(path)

                    if extension == '.avi':
                        print(f"{YELLOW}Skipping {humanName} as it has an unsupported .avi extension.{RESET}")
                        continue

                    # Trim the video and export as MP3
                    output_audio_file = f"{filename}.mp3"
                    try:
                        trim_video(path, output_audio_file, "30", humanName)
                    except Exception as e:
                        print(f"{RED}Error trimming video: {e}{RESET}")
                        continue  # Skip to the next file if there's an error

                    # Check if trimmed audio file exists
                    if not os.path.exists(output_audio_file):
                        print(f"{RED}Trimmed audio file not found: {output_audio_file}{RESET}")
                        continue  # Skip to the next file if the trimmed audio file is not found

                    # Detect language
                    language_code = detect_language(output_audio_file, endpoint)

                    if language_code and language_code != 'invalid':
                        if extension == '.mp4':
                            # Update language metadata for .mp4
                            corrected_output_file = f"{filename}_corrected.mp4"
                            update_language_metadata(path, corrected_output_file, language_code, humanName)

                            # Remove original file
                            os.remove(path)

                            # Rename corrected file to original filename
                            os.rename(corrected_output_file, path)
                        elif extension == '.mkv':
                            # Update language metadata for .mkv
                            update_language_metadata_mkv(path, language_code, humanName)
                        # Force Plex Analysis of processed episode
                        episode.analyze()

                    # Delete temporary audio file
                    os.remove(output_audio_file)
                    print(f"{GREEN}{BOLD}Processing for {humanName} completed.{RESET}\n")
                    
                    # Log successful processing
                    log_file_processing(humanName, "Language Metadata Updated Successfully", f"to {language_code}")

                else:
                    code = stream.languageCode 
                    print(f'{RED}Skipping {show} S{episode.seasonNumber}E{episode.index} because it has an invalid language code: {code}{RESET}')
                    # Log skipped file
                    log_file_processing(humanName, "Skipped", "due to invalid language code")

    except Exception as e:
        error_message = "An error occurred while running the script."
        report_error(error_message)
    finally:
        # Finish logging for the run
        finish_logging_run(start_time)

if __name__ == '__main__':
    main()
