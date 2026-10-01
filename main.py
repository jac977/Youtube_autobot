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

TOKEN_FILE = "token.json"

def setup_youtube_credentials():
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
    {"topic": "Space", "title": "Did you know this crazy Space Fact? 🌌 #Shorts #SpaceFacts", "script": "Did you know that space is completely silent? There is no atmosphere in space, which means sound has no way to travel."},
    {"topic": "Ocean", "title": "Terrifying Ocean Secret! 🌊 #Shorts #OceanLife", "script": "Did you know that over 80 percent of our ocean remains unmapped, unobserved, and completely unexplored?"},
    {"topic": "Mindset", "title": "Brain Psychological Trick! 🧠 #Shorts #Psychology", "script": "If you want someone to listen to you attentively, start your sentence with 'I shouldn't be telling you this, but...'"},
    {"topic": "Animal", "title": "Unbelievable Animal Fact! 🦁 #Shorts #Nature", "script": "Did you know that Octopuses have three hearts and blue blood? Two hearts pump blood to the gills, and one to the body."}
]

def generate_ai_content():
    print("[+] Engine 1: Generating Script...", flush=True)
    item = random.choice(FACTS_DATABASE)
    return item['title'], item['script'], item['topic']

# ==================== ENGINE 2: TTS VOICEOVER GENERATOR ====================
def generate_voiceover(text, output_file="voice.mp3"):
    print("[+] Engine 2: Generating Voiceover...", flush=True)
    tts = gTTS(text=text, lang='en', slow=False)
    tts.save(output_file)
    return output_file

# ==================== ENGINE 3: STOCK VIDEO DOWNLOADER ====================
def download_background_video(topic, output_file="bg_video.mp4"):
    print(f"[+] Engine 3: Fetching Background Video for '{topic}'...", flush=True)
    headers = {"Authorization": "563492ad6f91700001000001859cbf07ef944d188bd06d871785502c"}
    url = f"https://api.pexels.com/videos/search?query={topic}&orientation=portrait&per_page=5"
    
    try:
        r = requests.get(url, headers=headers, timeout=10)
        data = r.json()
        if data.get("videos"):
            video_files = random.choice(data["videos"])["video_files"]
            # Moderate resolution choosen to save RAM during FFmpeg merge
            sd_video = min(video_files, key=lambda x: abs((x.get("width") or 0) - 720))
            video_url = sd_video["link"]
            
            vid_data = requests.get(video_url, timeout=30).content
            with open(output_file, "wb") as f:
                f.write(vid_data)
            return output_file
    except Exception as e:
        print(f"[!] Stock video API error: {e}. Generating fallback solid color background.", flush=True)

    os.system(f"ffmpeg -y -f lavfi -i color=c=black:s=720x1280:r=30 -t 15 {output_file}")
    return output_file

# ==================== ENGINE 4: LOW-MEMORY FFMPEG MERGER ====================
def merge_media(video_file, audio_file, output_file="final_short.mp4"):
    """FFmpeg configured with strict low-memory optimization for 512MB RAM servers."""
    print("[+] Engine 4: Merging Audio and Video (Low-Memory Mode)...", flush=True)
    cmd = (
        f"ffmpeg -y -threads 1 -stream_loop -1 -i {video_file} -i {audio_file} "
        f"-c:v libx264 -preset ultrafast -tune zerolatency -crf 28 "
        f"-vf scale=720:1280 -shortest -map 0:v:0 -map 1:a:0 -pix_fmt yuv420p {output_file}"
    )
    os.system(cmd)
    return output_file

# ==================== ENGINE 5: YOUTUBE UPLOADER ====================
def upload_to_youtube(creds, video_file, title):
    print("[+] Engine 5: Connecting to YouTube API & Uploading...", flush=True)
    youtube = build("youtube", "v3", credentials=creds)
    
    body = {
        'snippet': {
            'title': title,
            'description': f"{title}\n\nAutomated AI Generated Short #Shorts #Viral",
            'tags': ['Shorts', 'AI', 'Facts', 'Viral'],
            'categoryId': '27'
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
    title, script_text, topic = generate_ai_content()
    audio_file = generate_voiceover(script_text)
    video_file = download_background_video(topic)
    final_output = merge_media(video_file, audio_file)
    upload_to_youtube(creds, final_output, title)

if __name__ == "__main__":
    while True:
        try:
            run_pipeline()
            print("[*] Pipeline finished successfully! Sleeping for 4 Hours...", flush=True)
            time.sleep(14400)
        except Exception as e:
            err_msg = str(e)
            print(f"[!] Pipeline Error: {err_msg}", flush=True)
            if "uploadLimitExceeded" in err_msg or "400" in err_msg:
                print("[!] Daily Upload Limit reached! Retrying after 1 Hour...", flush=True)
                time.sleep(3600)
            else:
                print("[!] Retrying pipeline in 60 seconds...", flush=True)
                time.sleep(60)
