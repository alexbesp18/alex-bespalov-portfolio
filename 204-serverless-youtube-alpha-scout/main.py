import os
from datetime import datetime, timezone, timedelta
import feedparser
from youtube_transcript_api import YouTubeTranscriptApi
from openai import OpenAI
from dotenv import load_dotenv
import resend

# Load environment variables (for local testing)
load_dotenv()

# Configuration
CHANNEL_ID = 'UCCpNQKYvrnWQNjZprabMJlw'  # Peter Diamandis
RSS_URL = f'https://www.youtube.com/feeds/videos.xml?channel_id={CHANNEL_ID}'

# AI Configuration (OpenRouter)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_MODEL = "x-ai/grok-4.1-fast"

# Email Configuration (Resend)
# DEFAULTS set for maximum convenience
EMAIL_SENDER = os.getenv('EMAIL_SENDER', 'onboarding@resend.dev')
EMAIL_RECEIVER = os.getenv('EMAIL_RECEIVER', 'ab00477@icloud.com')
resend.api_key = os.getenv('EMAIL_PASSWORD') # User provided key maps here

def get_latest_video():
    """Fetches the latest video from the RSS feed."""
    print("Fetching RSS feed...")
    feed = feedparser.parse(RSS_URL)
    
    if not feed.entries:
        print("No entries found in RSS feed.")
        return None

    entry = feed.entries[0]
    published_time = datetime.fromisoformat(entry.published).replace(tzinfo=timezone.utc)
    current_time = datetime.now(timezone.utc)
    
    # Check if published in the last 24 hours
    force_run = os.getenv('FORCE_RUN', 'false').lower() == 'true'
    if not force_run and (current_time - published_time > timedelta(hours=24)):
        print(f"Latest video '{entry.title}' was published more than 24 hours ago ({published_time}). Skipping.")
        return None
    
    if force_run:
        print(f"FORCE_RUN enabled. Processing video '{entry.title}' regardless of date.")
    
    print(f"Found new video: {entry.title} (ID: {entry.yt_videoid})")
    return {
        'id': entry.yt_videoid,
        'title': entry.title,
        'link': entry.link
    }

def get_transcript(video_id):
    """Fetches the transcript for a given video ID."""
    print(f"Fetching transcript for video ID: {video_id}...")
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        transcript_text = " ".join([t['text'] for t in transcript_list])
        return transcript_text
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return None

def analyze_transcript(transcript_text, video_title):
    """Analyzes the transcript using OpenRouter (Grok)."""
    print(f"Analyzing transcript with OpenRouter ({OPENROUTER_MODEL})...")
    
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

    # Prepare attachment if exists
    attachments = []
    if transcript_text:
        attachments.append({
            "filename": "transcript.txt",
            "content": list(transcript_text.encode('utf-8')) # Resend SDK expects a list of integers for bytes
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

def main():
    if not OPENROUTER_API_KEY:
        print("Error: OPENROUTER_API_KEY not found.")
        return

    video = get_latest_video()
    if not video:
        return

    transcript = get_transcript(video['id'])
    if not transcript:
        print("No transcript available. Skipping analysis.")
        return

    analysis_html = analyze_transcript(transcript, video['title'])
    if not analysis_html:
        print("Analysis failed.")
        return

    # Wrap analysis in a basic HTML structure with link to video
    final_html = f"""
    <html>
    <body>
        <h2>Alpha Scout Report: {video['title']}</h2>
        <p><a href="{video['link']}">Watch Video</a></p>
        <hr>
        {analysis_html}
    </body>
    </html>
    """

    send_email(f"Alpha Scout: {video['title']}", final_html, transcript)

if __name__ == '__main__':
    main()
