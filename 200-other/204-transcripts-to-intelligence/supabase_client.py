"""
Supabase persistence layer for storing and retrieving podcast analysis data.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from dataclasses import asdict
import json
import logging

logger = logging.getLogger(__name__)


class SupabaseClient:
    """Client for Supabase database operations."""
    
    def __init__(self, url: str = None, key: str = None):
        from supabase import create_client, Client
        from config.settings import get_settings
        
        settings = get_settings()
        self.url = url or settings.supabase.url
        self.key = key or settings.supabase.key
        
        if not self.url or not self.key:
            raise ValueError("Supabase URL and key are required")
        
        self.client: Client = create_client(self.url, self.key)
    
    # =========================================================================
    # PODCAST OPERATIONS
    # =========================================================================
    
    def create_podcast(
        self,
        youtube_id: str,
        url: str,
        title: str = None,
        channel_name: str = None,
        channel_id: str = None,
        duration_seconds: int = None,
        publish_date: datetime = None,
        description: str = None,
        thumbnail_url: str = None
    ) -> Dict[str, Any]:
        """Create a new podcast record."""
        data = {
            'youtube_id': youtube_id,
            'url': url,
            'title': title,
            'channel_name': channel_name,
            'channel_id': channel_id,
            'duration_seconds': duration_seconds,
            'publish_date': publish_date.isoformat() if publish_date else None,
            'description': description,
            'thumbnail_url': thumbnail_url,
            'status': 'pending'
        }
        
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
        
        result = self.client.table('podcasts').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_podcast(self, podcast_id: str = None, youtube_id: str = None) -> Optional[Dict]:
        """Get podcast by ID or YouTube ID."""
        query = self.client.table('podcasts').select('*')
        
        if podcast_id:
            query = query.eq('id', podcast_id)
        elif youtube_id:
            query = query.eq('youtube_id', youtube_id)
        else:
            raise ValueError("Either podcast_id or youtube_id required")
        
        result = query.execute()
        return result.data[0] if result.data else None
    
    def update_podcast_status(
        self,
        podcast_id: str,
        status: str,
        error_message: str = None,
        processing_time: float = None,
        transcription_cost: float = None,
        analysis_cost: float = None
    ) -> Dict:
        """Update podcast processing status."""
        data = {
            'status': status,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if error_message:
            data['error_message'] = error_message
        if processing_time:
            data['processing_time_seconds'] = processing_time
        if transcription_cost is not None:
            data['transcription_cost'] = transcription_cost
        if analysis_cost is not None:
            data['analysis_cost'] = analysis_cost
        if transcription_cost is not None or analysis_cost is not None:
            data['total_cost'] = (transcription_cost or 0) + (analysis_cost or 0)
        if status == 'completed':
            data['processed_at'] = datetime.utcnow().isoformat()
        
        result = self.client.table('podcasts').update(data).eq('id', podcast_id).execute()
        return result.data[0] if result.data else None
    
    # =========================================================================
    # TRANSCRIPT OPERATIONS
    # =========================================================================
    
    def save_transcript(
        self,
        podcast_id: str,
        full_text: str,
        method: str,
        confidence_score: float = None,
        language: str = 'en',
        whisper_model: str = None
    ) -> Dict:
        """Save transcript for a podcast."""
        data = {
            'podcast_id': podcast_id,
            'full_text': full_text,
            'word_count': len(full_text.split()),
            'method': method,
            'confidence_score': confidence_score,
            'language': language,
            'whisper_model': whisper_model
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        result = self.client.table('transcripts').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_transcript(self, podcast_id: str) -> Optional[Dict]:
        """Get transcript for a podcast."""
        result = self.client.table('transcripts').select('*').eq(
            'podcast_id', podcast_id
        ).execute()
        return result.data[0] if result.data else None
    
    # =========================================================================
    # SEGMENT OPERATIONS
    # =========================================================================
    
    def save_segments(self, podcast_id: str, segments: List[Dict]) -> List[Dict]:
        """Save multiple segments for a podcast."""
        data = []
        for seg in segments:
            data.append({
                'podcast_id': podcast_id,
                'segment_index': seg.get('segment_index'),
                'start_time_seconds': seg.get('start_seconds'),
                'end_time_seconds': seg.get('end_seconds'),
                'transcript_chunk': seg.get('transcript_chunk'),
                'key_topics': json.dumps(seg.get('topics', [])),
                'summary': seg.get('summary'),
                'direct_quote': seg.get('quote', {}).get('text'),
                'quote_speaker': seg.get('quote', {}).get('speaker')
            })
        
        result = self.client.table('segments').insert(data).execute()
        return result.data
    
    def get_segments(self, podcast_id: str) -> List[Dict]:
        """Get all segments for a podcast."""
        result = self.client.table('segments').select('*').eq(
            'podcast_id', podcast_id
        ).order('segment_index').execute()
        return result.data
    
    # =========================================================================
    # BUSINESS IDEAS OPERATIONS
    # =========================================================================
    
    def save_business_ideas(self, podcast_id: str, ideas: List[Dict]) -> List[Dict]:
        """Save business ideas for a podcast."""
        data = []
        for idea in ideas:
            data.append({
                'podcast_id': podcast_id,
                'idea_index': idea.get('index'),
                'title': idea.get('title'),
                'description': idea.get('description'),
                'hour_1_4': idea.get('plan_hours_1_4'),
                'hour_5_12': idea.get('plan_hours_5_12'),
                'hour_13_24': idea.get('plan_hours_13_24'),
                'supporting_quote': idea.get('supporting_quote', {}).get('text'),
                'quote_timestamp_seconds': idea.get('supporting_quote', {}).get('timestamp_seconds'),
                'estimated_startup_cost': idea.get('estimated_cost'),
                'target_market': idea.get('target_market')
            })
        
        result = self.client.table('business_ideas').insert(data).execute()
        return result.data
    
    def get_business_ideas(self, podcast_id: str) -> List[Dict]:
        """Get business ideas for a podcast."""
        result = self.client.table('business_ideas').select('*').eq(
            'podcast_id', podcast_id
        ).order('idea_index').execute()
        return result.data
    
    # =========================================================================
    # INVESTMENT THESIS OPERATIONS
    # =========================================================================
    
    def save_investment_theses(self, podcast_id: str, theses: List[Dict]) -> List[Dict]:
        """Save investment theses and stock picks for a podcast."""
        saved_theses = []
        
        for thesis in theses:
            # Save thesis
            thesis_data = {
                'podcast_id': podcast_id,
                'industry': thesis.get('industry'),
                'sub_industry': thesis.get('sub_industry'),
                'thesis_summary': thesis.get('thesis_summary'),
                'supporting_quote': thesis.get('supporting_quote', {}).get('text'),
                'catalyst_events': ', '.join(thesis.get('catalysts', [])),
                'time_horizon': thesis.get('time_horizon', '6-18 months')
            }
            
            thesis_result = self.client.table('investment_theses').insert(thesis_data).execute()
            thesis_record = thesis_result.data[0] if thesis_result.data else None
            
            if thesis_record:
                saved_theses.append(thesis_record)
                
                # Save associated stock picks
                stocks = thesis.get('stocks', [])
                if stocks:
                    stock_data = []
                    for stock in stocks:
                        stock_data.append({
                            'thesis_id': thesis_record['id'],
                            'podcast_id': podcast_id,
                            'ticker': stock.get('ticker'),
                            'company_name': stock.get('company_name'),
                            'exchange': stock.get('exchange'),
                            'is_validated': stock.get('is_validated', False),
                            'market_cap_billions': stock.get('market_cap_billions'),
                            'rationale': stock.get('rationale')
                        })
                    
                    self.client.table('stock_picks').insert(stock_data).execute()
        
        return saved_theses
    
    def get_investment_theses(self, podcast_id: str) -> List[Dict]:
        """Get investment theses with stock picks for a podcast."""
        theses = self.client.table('investment_theses').select('*').eq(
            'podcast_id', podcast_id
        ).execute().data
        
        # Get stock picks for each thesis
        for thesis in theses:
            stocks = self.client.table('stock_picks').select('*').eq(
                'thesis_id', thesis['id']
            ).execute().data
            thesis['stocks'] = stocks
        
        return theses
    
    # =========================================================================
    # LOGGING OPERATIONS
    # =========================================================================
    
    def log_processing_step(
        self,
        podcast_id: str,
        step: str,
        status: str,
        message: str = None,
        duration_ms: int = None
    ) -> Dict:
        """Log a processing step."""
        data = {
            'podcast_id': podcast_id,
            'step': step,
            'status': status,
            'message': message,
            'duration_ms': duration_ms
        }
        
        data = {k: v for k, v in data.items() if v is not None}
        result = self.client.table('processing_logs').insert(data).execute()
        return result.data[0] if result.data else None
    
    def get_processing_logs(self, podcast_id: str) -> List[Dict]:
        """Get processing logs for a podcast."""
        result = self.client.table('processing_logs').select('*').eq(
            'podcast_id', podcast_id
        ).order('created_at').execute()
        return result.data
    
    # =========================================================================
    # QUERY OPERATIONS
    # =========================================================================
    
    def list_podcasts(
        self,
        status: str = None,
        channel: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """List podcasts with optional filters."""
        query = self.client.table('podcasts').select('*')
        
        if status:
            query = query.eq('status', status)
        if channel:
            query = query.ilike('channel_name', f'%{channel}%')
        
        result = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
        return result.data
    
    def search_transcripts(self, search_term: str, limit: int = 10) -> List[Dict]:
        """Full-text search across transcripts."""
        # Note: Requires FTS index on transcripts.full_text
        result = self.client.table('transcripts').select(
            '*, podcasts!inner(title, channel_name, youtube_id)'
        ).ilike('full_text', f'%{search_term}%').limit(limit).execute()
        return result.data
    
    def get_stock_picks_by_ticker(self, ticker: str) -> List[Dict]:
        """Get all recommendations for a specific ticker."""
        result = self.client.table('stock_picks').select(
            '*, investment_theses!inner(industry, sub_industry, thesis_summary), '
            'podcasts!inner(title, channel_name, youtube_id)'
        ).eq('ticker', ticker.upper()).execute()
        return result.data


def get_supabase_client() -> SupabaseClient:
    """Get configured Supabase client."""
    return SupabaseClient()
