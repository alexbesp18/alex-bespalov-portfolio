"""
Unit tests for shared_core.notifications module.

Tests email client and HTML formatters.
"""

import pytest
from unittest import mock
import os

from shared_core.notifications import (
    EmailConfig,
    ResendEmailClient,
    format_html_table,
    format_html_section,
    format_html_list,
    format_action_link,
    format_subject,
    make_basic_html_email,
)


class TestEmailConfig:
    """Tests for EmailConfig dataclass."""
    
    def test_create_config(self):
        """Create EmailConfig with all fields."""
        config = EmailConfig(
            api_key='test-api-key',
            from_address='sender@example.com',
            to_addresses=['recipient@example.com'],
        )
        
        assert config.api_key == 'test-api-key'
        assert config.from_address == 'sender@example.com'
        assert config.to_addresses == ['recipient@example.com']
    
    def test_config_optional_fields(self):
        """EmailConfig with optional fields."""
        config = EmailConfig(
            api_key='test-key',
            from_address='sender@example.com',
            to_addresses=['recipient@example.com'],
            reply_to='reply@example.com',
        )
        
        assert config.reply_to == 'reply@example.com'
    
    def test_from_env(self):
        """EmailConfig from environment variables."""
        with mock.patch.dict(os.environ, {
            'RESEND_API_KEY': 'env-api-key',
            'EMAIL_FROM': 'from@example.com',
            'EMAIL_TO': 'to@example.com',
        }):
            config = EmailConfig.from_env()
            
            assert config.api_key == 'env-api-key'
            assert config.from_address == 'from@example.com'
            assert config.to_addresses == ['to@example.com']
    
    def test_from_env_missing(self):
        """EmailConfig.from_env with missing vars."""
        with mock.patch.dict(os.environ, {}, clear=True):
            config = EmailConfig.from_env()
            
            assert config is None


class TestResendEmailClient:
    """Tests for ResendEmailClient class."""
    
    @pytest.fixture
    def config(self):
        """Sample email config."""
        return EmailConfig(
            api_key='test-api-key',
            from_address='sender@example.com',
            to_addresses=['recipient@example.com'],
        )
    
    @pytest.fixture
    def client(self, config):
        """Sample email client."""
        return ResendEmailClient(config)
    
    def test_send_dry_run(self, client):
        """send() with dry_run doesn't call API."""
        result = client.send(
            subject='Test Subject',
            html='<p>Test content</p>',
            dry_run=True,
        )
        
        assert result is True
    
    def test_client_from_env(self):
        """Create client from environment variables."""
        with mock.patch.dict(os.environ, {
            'RESEND_API_KEY': 'env-api-key',
            'EMAIL_FROM': 'from@example.com',
            'EMAIL_TO': 'to@example.com',
        }):
            config = EmailConfig.from_env()
            assert config is not None
            
            client = ResendEmailClient(config)
            assert isinstance(client, ResendEmailClient)


class TestFormatHtmlTable:
    """Tests for format_html_table function."""
    
    def test_basic_table(self):
        """Create basic HTML table."""
        headers = ['Symbol', 'Price', 'Action']
        rows = [
            ['NVDA', 500.0, 'BUY'],
            ['AAPL', 150.0, 'SELL'],
        ]
        
        result = format_html_table(headers, rows)
        
        assert '<table' in result
        assert '</table>' in result
        assert 'NVDA' in result
        assert 'Symbol' in result
    
    def test_table_headers(self):
        """Table includes column headers."""
        headers = ['Symbol', 'Price']
        rows = [['AAPL', 150.0]]
        
        result = format_html_table(headers, rows)
        
        assert '<th' in result or '<thead' in result
        assert 'Symbol' in result
        assert 'Price' in result
    
    def test_empty_rows(self):
        """Handle empty rows list."""
        headers = ['Symbol', 'Price']
        result = format_html_table(headers, [])
        
        assert '<table' in result
        assert 'Symbol' in result
    
    def test_table_styling(self):
        """Table includes basic styling."""
        result = format_html_table(['Col'], [['Val']])
        
        assert 'style=' in result


class TestFormatHtmlSection:
    """Tests for format_html_section function."""
    
    def test_basic_section(self):
        """Create basic HTML section."""
        result = format_html_section(
            title='Test Section',
            items=['Item 1', 'Item 2']
        )
        
        assert 'Test Section' in result
        assert 'Item 1' in result
        assert 'Item 2' in result
    
    def test_section_with_color(self):
        """Section with color parameter."""
        result = format_html_section(
            title='Alerts',
            items=['Alert 1'],
            color='buy'
        )
        
        assert 'Alerts' in result
    
    def test_empty_items(self):
        """Section with empty items list."""
        result = format_html_section(title='Empty', items=[])
        assert 'Empty' in result


class TestFormatHtmlList:
    """Tests for format_html_list function."""
    
    def test_basic_list(self):
        """Create basic HTML list."""
        items = [{'name': 'Item 1'}, {'name': 'Item 2'}]
        
        result = format_html_list(items)
        
        assert '<ul' in result
    
    def test_with_format_func(self):
        """List with custom format function."""
        items = [{'name': 'AAPL'}, {'name': 'NVDA'}]
        
        result = format_html_list(items, format_func=lambda x: x['name'])
        
        assert 'AAPL' in result
        assert 'NVDA' in result
    
    def test_empty_list(self):
        """Handle empty list."""
        result = format_html_list([])
        
        assert '<ul' in result


class TestFormatActionLink:
    """Tests for format_action_link function."""
    
    def test_basic_link(self):
        """Create basic action link."""
        result = format_action_link(
            ticker='AAPL',
            action='BUY',
        )
        
        # Without base_url, returns plain text
        assert 'AAPL' in result
        assert 'BUY' in result
    
    def test_link_with_url(self):
        """Action link with base URL."""
        result = format_action_link(
            ticker='AAPL',
            action='BUY',
            base_url='https://example.com'
        )
        
        assert '<a' in result
        assert 'href="https://example.com' in result


class TestFormatSubject:
    """Tests for format_subject function."""
    
    def test_buy_sell_counts(self):
        """Subject includes buy/sell counts."""
        signals = [
            {'action': 'BUY'},
            {'action': 'BUY'},
            {'action': 'SELL'},
        ]
        result = format_subject(signals)
        
        assert '2 BUY' in result
        assert '1 SELL' in result
    
    def test_buy_only(self):
        """Subject with only buys."""
        signals = [{'action': 'BUY'}, {'action': 'BUY'}]
        result = format_subject(signals)
        
        assert '2 BUY' in result
    
    def test_modes(self):
        """Subject with different modes."""
        signals = [{'action': 'BUY'}]
        
        alert = format_subject(signals, mode='alert')
        reminder = format_subject(signals, mode='reminder')
        digest = format_subject(signals, mode='digest')
        
        assert 'Alert' in alert
        assert 'Reminder' in reminder
        assert 'Digest' in digest
    
    def test_empty_signals(self):
        """Subject with no signals."""
        result = format_subject([])
        
        assert isinstance(result, str)
        assert 'No signals' in result


class TestMakeBasicHtmlEmail:
    """Tests for make_basic_html_email function."""
    
    def test_valid_html(self):
        """Creates valid HTML email."""
        result = make_basic_html_email(
            title='Test Email',
            body_html='<p>Email body content</p>'
        )
        
        assert '<html' in result.lower()
        assert '</html>' in result.lower()
        assert 'Email body content' in result
    
    def test_includes_title(self):
        """Email includes title."""
        result = make_basic_html_email(
            title='My Alert Title',
            body_html='<p>Content</p>'
        )
        
        assert 'My Alert Title' in result
    
    def test_includes_body(self):
        """Email includes body content."""
        result = make_basic_html_email(
            title='Test',
            body_html='<div>Custom content here</div>'
        )
        
        assert 'Custom content here' in result
    
    def test_styling(self):
        """Email includes basic styling."""
        result = make_basic_html_email(
            title='Test',
            body_html='<p>Content</p>'
        )
        
        assert 'style' in result.lower()
    
    def test_with_footer(self):
        """Email with footer."""
        result = make_basic_html_email(
            title='Test',
            body_html='<p>Content</p>',
            footer='Footer content'
        )
        
        assert 'Footer content' in result


class TestNotificationEdgeCases:
    """Edge case tests for notifications."""
    
    def test_unicode_content(self):
        """Unicode content is preserved."""
        result = format_html_section(
            title='Émoji Test 🚀',
            items=['日本語']
        )
        
        assert '🚀' in result or 'Émoji' in result
    
    def test_long_content(self):
        """Long content is handled."""
        long_content = '<p>' + 'x' * 10000 + '</p>'
        
        result = make_basic_html_email(
            title='Test',
            body_html=long_content
        )
        
        assert len(result) > 10000
    
    def test_table_numeric_formatting(self):
        """Numeric values in tables are formatted properly."""
        headers = ['Price', 'Volume']
        rows = [[123.456789, 1000000]]
        
        result = format_html_table(headers, rows)
        
        assert '123' in result
