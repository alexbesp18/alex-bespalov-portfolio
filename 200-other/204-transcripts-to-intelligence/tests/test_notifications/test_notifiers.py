"""
Tests for Notification Module

Tests all notification channels (Slack, Discord, Email) using mocked HTTP.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.notifications import (
    SlackNotifier,
    DiscordNotifier,
    EmailNotifier,
    NotificationManager,
    NotificationResult,
)
from src.notifications.base import NotificationLevel


class TestSlackNotifier:
    """Tests for SlackNotifier."""
    
    def test_not_configured_without_webhook(self):
        """Test that notifier reports not configured without webhook."""
        notifier = SlackNotifier(webhook_url=None)
        assert not notifier.is_configured()
    
    def test_configured_with_webhook(self):
        """Test that notifier reports configured with webhook."""
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        assert notifier.is_configured()
    
    def test_send_returns_error_when_not_configured(self):
        """Test sending returns error when not configured."""
        notifier = SlackNotifier(webhook_url=None)
        result = notifier.send("Test message")
        
        assert not result.success
        assert "not configured" in result.error.lower()
    
    @patch('requests.post')
    def test_send_success(self, mock_post):
        """Test successful notification send."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.text = "ok"
        mock_post.return_value.raise_for_status = MagicMock()
        
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        result = notifier.send("Test message", title="Test Title")
        
        assert result.success
        assert result.channel == "slack"
        mock_post.assert_called_once()
    
    @patch('requests.post')
    def test_send_includes_details(self, mock_post):
        """Test that send includes details in payload."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        notifier.send(
            "Test message",
            title="Test",
            details={"key1": "value1", "key2": "value2"}
        )
        
        # Check that the post was called with JSON containing blocks
        call_args = mock_post.call_args
        assert "json" in call_args.kwargs
        assert "blocks" in call_args.kwargs["json"]
    
    @patch('requests.post')
    def test_send_failure(self, mock_post):
        """Test handling of send failure."""
        mock_post.side_effect = Exception("Network error")
        
        notifier = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        result = notifier.send("Test message")
        
        assert not result.success
        assert "Network error" in result.error
    
    def test_send_success_convenience(self):
        """Test send_success convenience method."""
        notifier = SlackNotifier(webhook_url=None)
        result = notifier.send_success("Success message")
        
        # Should fail because not configured, but should not crash
        assert not result.success
    
    def test_send_error_convenience(self):
        """Test send_error convenience method."""
        notifier = SlackNotifier(webhook_url=None)
        result = notifier.send_error("Error message")
        
        assert not result.success


class TestDiscordNotifier:
    """Tests for DiscordNotifier."""
    
    def test_not_configured_without_webhook(self):
        """Test that notifier reports not configured without webhook."""
        notifier = DiscordNotifier(webhook_url=None)
        assert not notifier.is_configured()
    
    def test_configured_with_webhook(self):
        """Test that notifier reports configured with webhook."""
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        assert notifier.is_configured()
    
    @patch('requests.post')
    def test_send_success(self, mock_post):
        """Test successful notification send."""
        mock_post.return_value.status_code = 204
        mock_post.return_value.text = ""
        mock_post.return_value.raise_for_status = MagicMock()
        
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        result = notifier.send("Test message", level=NotificationLevel.SUCCESS)
        
        assert result.success
        assert result.channel == "discord"
    
    @patch('requests.post')
    def test_send_uses_embeds(self, mock_post):
        """Test that Discord uses embeds format."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        notifier = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        notifier.send("Test", title="Title", details={"key": "value"})
        
        call_args = mock_post.call_args
        assert "embeds" in call_args.kwargs["json"]


class TestEmailNotifier:
    """Tests for EmailNotifier."""
    
    def test_not_configured_without_credentials(self):
        """Test that notifier reports not configured without credentials."""
        notifier = EmailNotifier(to_email="test@example.com")
        assert not notifier.is_configured()
    
    def test_not_configured_without_recipient(self):
        """Test that notifier reports not configured without recipient."""
        notifier = EmailNotifier(sendgrid_api_key="test_key")
        assert not notifier.is_configured()
    
    def test_configured_with_sendgrid(self):
        """Test that notifier reports configured with SendGrid."""
        notifier = EmailNotifier(
            to_email="test@example.com",
            sendgrid_api_key="test_key"
        )
        assert notifier.is_configured()
    
    def test_configured_with_smtp(self):
        """Test that notifier reports configured with SMTP."""
        notifier = EmailNotifier(
            to_email="test@example.com",
            smtp_host="smtp.example.com",
            smtp_user="user",
            smtp_password="password"
        )
        assert notifier.is_configured()
    
    @patch('requests.post')
    def test_send_via_sendgrid(self, mock_post):
        """Test sending via SendGrid API."""
        mock_post.return_value.status_code = 202
        mock_post.return_value.raise_for_status = MagicMock()
        
        notifier = EmailNotifier(
            to_email="test@example.com",
            sendgrid_api_key="SG.test_key"
        )
        result = notifier.send("Test message", title="Test Subject")
        
        assert result.success
        assert result.channel == "email"
        
        # Verify SendGrid API was called
        call_args = mock_post.call_args
        assert "sendgrid.com" in call_args.args[0]


class TestNotificationManager:
    """Tests for NotificationManager."""
    
    def test_no_channels_configured(self):
        """Test manager with no channels configured."""
        manager = NotificationManager(auto_configure=False)
        assert not manager.has_channels()
        assert manager.configured_channels == []
    
    def test_configured_channels_list(self):
        """Test that configured channels are listed."""
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        manager = NotificationManager(slack=slack, auto_configure=False)
        
        assert manager.has_channels()
        assert "slack" in manager.configured_channels
    
    @patch('requests.post')
    def test_notify_all_sends_to_all_channels(self, mock_post):
        """Test that notify_all sends to all configured channels."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        discord = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        
        manager = NotificationManager(
            slack=slack,
            discord=discord,
            auto_configure=False
        )
        
        results = manager.notify_all("Test message")
        
        assert len(results) == 2
        assert all(r.success for r in results)
    
    @patch('requests.post')
    def test_notify_specific_channels(self, mock_post):
        """Test sending to specific channels only."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        discord = DiscordNotifier(webhook_url="https://discord.com/api/webhooks/test")
        
        manager = NotificationManager(
            slack=slack,
            discord=discord,
            auto_configure=False
        )
        
        results = manager.notify_all("Test", channels=["slack"])
        
        assert len(results) == 1
        assert results[0].channel == "slack"
    
    @patch('requests.post')
    def test_notify_success_convenience(self, mock_post):
        """Test notify_success convenience method."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        manager = NotificationManager(slack=slack, auto_configure=False)
        
        results = manager.notify_success("Success!")
        
        assert len(results) == 1
        assert results[0].success
    
    @patch('requests.post')
    def test_notify_processing_complete(self, mock_post):
        """Test the processing complete notification."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        manager = NotificationManager(slack=slack, auto_configure=False)
        
        results = manager.notify_processing_complete(
            videos_processed=5,
            total_cost=0.50,
            errors=0,
            output_dir="/path/to/outputs"
        )
        
        assert len(results) == 1
        assert results[0].success
    
    @patch('requests.post')
    def test_notify_processing_failed(self, mock_post):
        """Test the processing failed notification."""
        mock_post.return_value.status_code = 200
        mock_post.return_value.raise_for_status = MagicMock()
        
        slack = SlackNotifier(webhook_url="https://hooks.slack.com/test")
        manager = NotificationManager(slack=slack, auto_configure=False)
        
        results = manager.notify_processing_failed(
            error="API rate limit exceeded",
            video_url="https://youtube.com/watch?v=test"
        )
        
        assert len(results) == 1


class TestNotificationResult:
    """Tests for NotificationResult dataclass."""
    
    def test_to_dict(self):
        """Test result serialization."""
        result = NotificationResult(
            success=True,
            channel="slack",
            error=None,
            response="ok"
        )
        
        d = result.to_dict()
        
        assert d["success"] is True
        assert d["channel"] == "slack"
        assert d["error"] is None
    
    def test_failed_result(self):
        """Test failed result."""
        result = NotificationResult(
            success=False,
            channel="discord",
            error="Connection timeout"
        )
        
        assert not result.success
        assert result.error == "Connection timeout"

