import os
import json
import time
import random
import base64
import requests
from gtts import gTTS
import google.oauth2.credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# ==================== ENVIRONMENT CONFIGURATION ====================
GITHUB_TOKEN = os.getenv("Github_Token") or os.getenv("GITHUB_TOKEN")
YOUTUBE_TOKEN_JSON = os.getenv("YOUTUBE_TOKEN_JSON")
YOUTUBE_TOKEN_BASE64 = os.getenv("YOUTUBE_TOKEN_BASE64")

# Fallback check for token.json file
TOKEN_FILE = "token.json"

def setup_youtube_credentials():
    """Environment variables ya file se token recover karta hai."""
    if os.path.exists(TOKEN_FILE):
        return google.oauth2.credentials.Credentials.from_authorized_user_file(TOKEN_FILE)
    
    token_str = None
    if YOUTUBE_TOKEN_JSON:
        token_str = YOUTUBE_TOKEN_JSON
    elif YOUTUBE_TOKEN_BASE64:
        token_str = base64.b64decode(YOUTUBE_TOKEN_BASE64).decode('utf-8')
        
    if token_str:
        token_info = json.loads(token_str)
        with open(TOKEN_FILE, 'w') as f:
            f.write(token_str)
        return google.oauth2.credentials.Credentials.from_authorized_user_info(token_info)
    
    raise Exception("[-] YouTube Credentials Not Found! Set YOUTUBE_TOKEN_JSON in Render.")

# ==================== ENGINE 1: AI CONTENT GENERATOR ====================
FACTS_DATABASE = [
    {"topic": "Space", "title": "Did you know this crazy Space Fact? 🌌 #Shorts #SpaceFacts", "script": "Did you know that space is completely silent? There is no atmosphere in space, which means that sound has no medium or way to travel to be heard."},
    {"topic": "Ocean", "title": "Terrifying Ocean Secret! 🌊 #Shorts #OceanLife", "script": "Did you know that we have better maps of the surface of Mars and the Moon than we do of the Earth's ocean floor? More than 80 percent of our ocean remains unmapped and unexplored."},
    {"topic": "Mindset", "title": "Brain Psychological Trick! 🧠 #Shorts #Psychology", "script": "If you want someone to listen to you attentively, start your sentence with 'I shouldn't be telling you this, but...' The human brain naturally craves secrets."},
    {"topic": "Animal", "title": "Unbelievable Animal Fact! 🦁 #Shorts #Nature", "script": "Did you know that Octopuses have three hearts and blue blood? Two hearts pump blood to the gills, while the third pumps it to the rest of the body."}
]

def generate_ai_content():
    """AI Script select aur Generate karta hai."""
    print("[+] Engine 1: Generating Script...", flush=True)
    item = random.choice(FACTS_DATABASE)
    return item['title'], item['script'], item['topic']

# ==================== ENGINE 2: TTS VOICEOVER GENERATOR ====================
def generate_voiceover(text, output_file="voice.mp3"):
    """Text-to-Speech audio create karta hai."""
    print("[+] Engine 2: Generating Voiceover...", flush=True)
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_file)
    return output_file

# ==================== ENGINE 3: STOCK VIDEO DOWNLOADER ====================
def download_background_video(topic, output_file="bg_video.mp4"):
    """Pexels Free HD Portrait Stock Videos Fetch & Download karta hai."""
    print(f"[+] Engine 3: Fetching Background Video for '{topic}'...", flush=True)
    headers = {"Authorization": "563492ad6f91700001000001859cbf07ef944d188bd06d871785502c"}  # Free Public Pexels Key
    url = f"https://api.pexels.com/videos/search?query={topic}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("videos"):
            video_files = random.choice(data["videos"])["video_files"]
            # Highest resolution link choose karna
            hd_video = min(video_files, key=lambda x: abs((x.get("width") or 0) - 1080))
            video_url = hd_video["link"]
            
            vid_data = requests.get(video_url, timeout=30).content
            with open(output_file, "wb") as f:
                f.write(vid_data)
            return output_file
    except Exception as e:
        print(f"[!] Stock video API error: {e}. Generating fallback solid color background.", flush=True)

    # Fallback FFmpeg video generation if network fails
    os.system(f"ffmpeg -y -f lavfi -i color=c=black:s=1080x1920:r=30 -t 15 {output_file}")
    return output_file

# ==================== ENGINE 4: FFMPEG MEDIA MERGER ====================
def merge_media(video_file, audio_file, output_file="final_short.mp4"):
    """Audio aur Video ko dynamic looping ke sath merge karta hai."""
    print("[+] Engine 4: Merging Audio and Video using FFmpeg...", flush=True)
    cmd = (
        f"ffmpeg -y -stream_loop -1 -i {video_file} -i {audio_file} "
        f"-c:v libx264 -shortest -map 0:v:0 -map 1:a:0 -pix_fmt yuv420p {output_file}"
    )
    os.system(cmd)
    return output_file

# ==================== ENGINE 5: YOUTUBE UPLOADER ====================
def upload_to_youtube(creds, video_file, title):
    """YouTube API Standard Uploader Engine."""
    print("[+] Engine 5: Connecting to YouTube API & Uploading...", flush=True)
    youtube = build("youtube", "v3", credentials=creds)
    
    body = {
        'snippet': {
            'title': title,
            'description': f"{title}\n\nAutomated AI Generated Short #Shorts #Viral",
            'tags': ['Shorts', 'AI', 'Facts', 'Viral'],
            'categoryId': '27' # Education
        },
        'status': {
            'privacyStatus': 'public',
            'selfDeclaredMadeForKids': False,
        }
    }
    
    media = MediaFileUpload(video_file, chunksize=-1, resumable=True, mimetype="video/mp4")
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            print(f"[*] Uploading progress: {int(status.progress() * 100)}%", flush=True)
            
    video_id = response.get('id')
    video_url = f"https://youtu.be/{video_id}"
    print(f"\n[✓] SUCCESS! Published Short: {video_url}\n", flush=True)
    return video_url

# ==================== MAIN AUTOMATION PIPELINE ====================
def run_pipeline():
    print("\n==================================================", flush=True)
    print("      YOUTUBE AUTOBOT - STARTING PIPELINE        ", flush=True)
    print("==================================================\n", flush=True)
    
    creds = setup_youtube_credentials()
    
    # 1. Generate Script
    title, script_text, topic = generate_ai_content()
    
    # 2. TTS Voice
    audio_file = generate_voiceover(script_text)
    
    # 3. Stock Background
    video_file = download_background_video(topic)
    
    # 4. Merge Media
    final_output = merge_media(video_file, audio_file)
    
    # 5. Upload Video
    upload_to_youtube(creds, final_output, title)

if __name__ == "__main__":
    while True:
        try:
            run_pipeline()
            print("[*] Pipeline finished successfully! Sleeping for 4 Hours before next upload...", flush=True)
            time.sleep(14400) # 4 Hours Sleep Interval
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Pipeline Error: {err_msg}", flush=True)
            if "uploadLimitExceeded" in err_msg or "400" in err_msg:
                print("[!] Daily Upload Limit reached! Retrying after 1 Hour...", flush=True)
                time.sleep(3600)
            else:
                print("[!] Retrying pipeline in 60 seconds...", flush=True)
                time.sleep(60)
