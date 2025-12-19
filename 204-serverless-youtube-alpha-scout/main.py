import os
import glob
from datetime import datetime, timezone, timedelta
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv
import resend
import yt_dlp
import whisper

# Load environment variables (for local testing)
load_dotenv()

# ==========================================
# CONFIGURATION
# ==========================================
CHANNEL_ID = 'UCCpNQKYvrnWQNjZprabMJlw'  # Peter Diamandis
RSS_URL = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'

# AI Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = "x-ai/grok-4.1-fast"

# Email Configuration (Resend)
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'onboarding@resend.dev')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER', 'ab00477@icloud.com')
resend.api_key = os.getenv('EMAIL_PASSWORD')

# ==========================================
# CORE FUNCTIONS
# ==========================================

def get_latest_video():
    """Fetches the latest video from the YouTube RSS feed."""
    print(f"Fetching RSS feed from: {RSS_URL}")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("No entries found in RSS feed.")
        return None

    entry = feed.entries[0]
    # Parse published time (standard ISO from YouTube RSS)
    published_time = datetime.fromisoformat(entry.published).replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    
    video_info = {
        'id': entry.yt_videoid,
        'title': entry.title,
        'link': entry.link,
        'published': published_time
    }

    # Check force_run environment variable (defaults to false)
    force_run = os.getenv('FORCE_RUN', 'false').lower() == 'true'
    
    if force_run:
        print(f"FORCE_RUN enabled. Processing video '{entry.title}' regardless of date.")
        return video_info

    # Default 24-hour check
    if current_time - published_time > timedelta(hours=24):
        print(f"Latest video '{entry.title}' was published more than 24 hours ago ({published_time}). Skipping.")
        return None
    
    print(f"Found new video: {entry.title} (ID: {entry.yt_videoid})")
    return video_info

def download_audio(video_id):
    """
    Downloads audio from YouTube video using yt-dlp.
    Returns path to the temporary mp3 file.
    """
    print(f"Downloading audio for video {video_id} using yt-dlp...")
    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Configure yt-dlp to extract audio and convert to mp3
    # Use 'android' client to bypass "Sign in to confirm you're not a bot"
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': 'temp_audio.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
        }],
        'quiet': True,
        'no_warnings': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists("temp_audio.mp3"):
            return "temp_audio.mp3"
        print("Error: Audio file not found after download.")
        return None
    except Exception as e:
        print(f"Error downloading audio: {e}")
        return None

def transcribe_with_local_whisper(audio_path):
    """
    Transcribes audio file using the local OpenAI Whisper model.
    Runs on CPU, requires no API key.
    """
    print("Transcribing audio with Local Whisper (model='base')... this may take a few minutes.")
    
    try:
        # Load the model (first run will download it, ~140MB)
        model = whisper.load_model("base")
        
        # Transcribe
        result = model.transcribe(audio_path)
        return result['text']
    except Exception as e:
        print(f"Error transcribing with Local Whisper: {e}")
        return None
    finally:
        # Cleanup temporary file
        if os.path.exists(audio_path):
            os.remove(audio_path)
            print(f"Cleaned up {audio_path}")

def get_transcript(video_id):
    """
    Fetches transcript.
    Strategy:
    1. Try standard YouTubeTranscriptApi (fastest).
    2. If failed (e.g., subtitles disabled), fallback to download + local whisper.
    """
    print(f"Fetching transcript for video ID: {video_id}...")
    
    # Attempt 1: Standard API
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([t['text'] for t in transcript_list])
        print("Successfully fetched transcript via Standard API.")
        return transcript_text
    except Exception as e:
        print(f"Standard transcript API failed: {e}")
        print("Falling back to Local Whisper transcription...")

    # Attempt 2: Local Whisper Fallback
    audio_path = download_audio(video_id)
    if audio_path:
        return transcribe_with_local_whisper(audio_path)
    
    return None

def analyze_transcript(transcript_text, video_title):
    """Analyzes the transcript using OpenRouter (Grok)."""
    print(f"Analyzing transcript with OpenRouter ({OPENROUTER_MODEL})...")
    
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY is missing.")
        return None

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY
    )
    
    system_prompt = (
        "You are a Buy-Side Equity Analyst. Analyze this transcript of a Peter Diamandis Moonshots episode. "
        "Output structured HTML. "
        "1) **3-Minute Breakdown**: Summarize key insights in strictly 3-minute time buckets (e.g., 0-3m, 3-6m, etc.). "
        "2) **Investment Alpha**: Extract 5-10 specific, high-signal 'Investing Alphas' (tickers, sectors, technology predictions). "
        "Do not be vague. Be actionable."
    )
    
    try:
        # Truncate transcript to avoid token limits (approx 100k chars is plenty for 1 hr video)
        response = client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Video Title: {video_title}\n\nTranscript:\n{transcript_text[:100000]}"}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error analyzing transcript: {e}")
        return None

def send_email(subject, html_content, transcript_text=None):
    """Sends an email using the Resend Python SDK."""
    print(f"Sending email from {EMAIL_SENDER} to {EMAIL_RECEIVER} via Resend SDK...")
    
    if not resend.api_key:
        print("Error: Resend API Key (EMAIL_PASSWORD) not found.")
        return

    # Prepare attachment if transcript is provided
    attachments = []
    if transcript_text:
        attachments.append({
            "filename": "transcript.txt",
            "content": list(transcript_text.encode('utf-8'))
        })

    params = {
        "from": EMAIL_SENDER,
        "to": [EMAIL_RECEIVER],
        "subject": subject,
        "html": html_content,
        "attachments": attachments
    }

    try:
        email = resend.Emails.send(params)
        print(f"Email sent successfully. ID: {email.get('id')}")
    except Exception as e:
        print(f"Error sending email: {e}")

# ==========================================
# MAIN EXECUTION
# ==========================================

def main():
    # 1. Validation
    if not OPENROUTER_API_KEY:
        print("CRITICAL: OPENROUTER_API_KEY not found in environment.")
        return

    # 2. Get Video
    video = get_latest_video()
    if not video:
        print("Exiting: No video to process.")
        return

    # 3. Get Transcript (with Fallback)
    transcript = get_transcript(video['id'])
    if not transcript:
        print("CRITICAL: Failed to obtain transcript via any method. Exiting.")
        return

    # 4. Analyze
    analysis_html = analyze_transcript(transcript, video['title'])
    if not analysis_html:
        print("CRITICAL: Analysis failed. Exiting.")
        return

    # 5. Format & Send
    final_html = f"""
    <html>
    <body>
        <h2>Alpha Scout Report: {video['title']}</h2>
        <p><a href="{video['link']}">Watch Video</a></p>
        <p><em>Generated by Serverless Alpha Scout (Grok + Whisper Fallback)</em></p>
        <hr>
        {analysis_html}
    </body>
    </html>
    """

    send_email(f"Alpha Scout: {video['title']}", final_html, transcript)
    print("Job Complete.")

if __name__ == '__main__':
    main()
