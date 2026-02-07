"""Tests for the metrics module."""

import time
from unittest.mock import patch

import pytest

from jamie.shared.metrics import MetricsCollector, get_metrics, reset_metrics


@pytest.fixture(autouse=True)
def reset_metrics_fixture():
    """Reset metrics before each test."""
    reset_metrics()
    yield
    reset_metrics()


class TestMetricsCollector:
    """Tests for MetricsCollector class."""
    
    def test_initial_state(self):
        """Test collector starts with zero counts."""
        collector = MetricsCollector()
        stats = collector.get_stats()
        
        assert stats["streams"]["total"] == 0
        assert stats["streams"]["active"] == 0
        assert stats["streams"]["success"] == 0
        assert stats["streams"]["failed"] == 0
        assert stats["streams"]["success_rate_percent"] == 0.0
    
    def test_stream_started(self):
        """Test recording stream start."""
        collector = MetricsCollector()
        collector.stream_started("session-1")
        
        assert collector.get_active_count() == 1
        stats = collector.get_stats()
        assert stats["streams"]["total"] == 1
        assert stats["streams"]["active"] == 1
        assert "session-1" in stats["active_sessions"]
    
    def test_stream_completed_success(self):
        """Test recording successful stream completion."""
        collector = MetricsCollector()
        collector.stream_started("session-1")
        collector.stream_completed("session-1", success=True)
        
        stats = collector.get_stats()
        assert stats["streams"]["total"] == 1
        assert stats["streams"]["active"] == 0
        assert stats["streams"]["success"] == 1
        assert stats["streams"]["failed"] == 0
        assert stats["streams"]["success_rate_percent"] == 100.0
    
    def test_stream_completed_failure(self):
        """Test recording failed stream completion."""
        collector = MetricsCollector()
        collector.stream_started("session-1")
        collector.stream_completed("session-1", success=False, error_code="TimeoutError")
        
        stats = collector.get_stats()
        assert stats["streams"]["failed"] == 1
        assert stats["streams"]["success_rate_percent"] == 0.0
        assert stats["errors"]["TimeoutError"] == 1
    
    def test_success_rate_calculation(self):
        """Test success rate calculation with mixed results."""
        collector = MetricsCollector()
        
        # 3 success, 1 failure = 75% success rate
        for i in range(3):
            collector.stream_started(f"success-{i}")
            collector.stream_completed(f"success-{i}", success=True)
        
        collector.stream_started("failure-1")
        collector.stream_completed("failure-1", success=False)
        
        stats = collector.get_stats()
        assert stats["streams"]["success_rate_percent"] == 75.0
    
    def test_latency_tracking(self):
        """Test latency/duration tracking."""
        collector = MetricsCollector()
        
        with patch("time.time") as mock_time:
            # Start at t=0
            mock_time.return_value = 0.0
            collector.stream_started("session-1")
            
            # Complete at t=5.0 (5 second duration)
            mock_time.return_value = 5.0
            collector.stream_completed("session-1", success=True)
        
        stats = collector.get_stats()
        assert stats["latency_seconds"]["avg"] == 5.0
        assert stats["latency_seconds"]["p50"] == 5.0
    
    def test_multiple_active_sessions(self):
        """Test tracking multiple concurrent sessions."""
        collector = MetricsCollector()
        
        collector.stream_started("session-1")
        collector.stream_started("session-2")
        collector.stream_started("session-3")
        
        assert collector.get_active_count() == 3
        
        collector.stream_completed("session-2", success=True)
        
        assert collector.get_active_count() == 2
        stats = collector.get_stats()
        assert "session-1" in stats["active_sessions"]
        assert "session-2" not in stats["active_sessions"]
        assert "session-3" in stats["active_sessions"]
    
    def test_prometheus_export(self):
        """Test Prometheus format export."""
        collector = MetricsCollector()
        collector.stream_started("session-1")
        collector.stream_completed("session-1", success=True)
        collector.stream_started("session-2")
        collector.stream_completed("session-2", success=False, error_code="NetworkError")
        
        prometheus = collector.to_prometheus()
        
        # Check metric declarations
        assert "# HELP jamie_streams_total" in prometheus
        assert "# TYPE jamie_streams_total counter" in prometheus
        assert "jamie_streams_total 2" in prometheus
        
        assert "jamie_streams_success_total 1" in prometheus
        assert "jamie_streams_failed_total 1" in prometheus
        
        # Check error labels
        assert 'jamie_errors_total{code="NetworkError"} 1' in prometheus
    
    def test_uptime_tracking(self):
        """Test uptime is tracked from collector creation."""
        with patch("time.time") as mock_time:
            mock_time.return_value = 1000.0
            collector = MetricsCollector()
            
            mock_time.return_value = 1060.0  # 60 seconds later
            stats = collector.get_stats()
            
            assert stats["uptime_seconds"] == 60.0


class TestGlobalMetrics:
    """Tests for global metrics instance."""
    
    def test_get_metrics_singleton(self):
        """Test get_metrics returns same instance."""
        m1 = get_metrics()
        m2 = get_metrics()
        assert m1 is m2
    
    def test_reset_metrics(self):
        """Test reset_metrics creates new instance."""
        m1 = get_metrics()
        m1.stream_started("session-1")
        
        reset_metrics()
        m2 = get_metrics()
        
        assert m1 is not m2
        assert m2.get_active_count() == 0
