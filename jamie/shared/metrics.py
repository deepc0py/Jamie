"""Lightweight metrics collection for Jamie observability.

Tracks key operational metrics in-memory with optional Prometheus export.
No external dependencies required.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from threading import Lock
from typing import Dict, Deque, Optional, List

from jamie.shared.logging import get_logger

log = get_logger(__name__)


class MetricType(str, Enum):
    """Types of metrics we track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"


@dataclass
class StreamMetrics:
    """Metrics for a single stream session."""
    session_id: str
    start_time: float
    end_time: Optional[float] = None
    success: Optional[bool] = None
    error_code: Optional[str] = None
    status_history: List[str] = field(default_factory=list)
    
    @property
    def duration_seconds(self) -> Optional[float]:
        """Get stream duration in seconds."""
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time


class MetricsCollector:
    """Thread-safe metrics collector for Jamie.
    
    Tracks:
    - Stream counts (total, active, success, failure)
    - Latency metrics (start time, duration)
    - Error rates and codes
    
    Maintains a rolling window of recent streams for rate calculations.
    """
    
    # Rolling window size for rate calculations
    WINDOW_SIZE = 1000
    
    def __init__(self):
        self._lock = Lock()
        self._start_time = time.time()
        
        # Counters
        self._streams_total = 0
        self._streams_success = 0
        self._streams_failed = 0
        
        # Active sessions
        self._active_streams: Dict[str, StreamMetrics] = {}
        
        # Rolling window for rate calculations
        self._recent_streams: Deque[StreamMetrics] = deque(maxlen=self.WINDOW_SIZE)
        
        # Latency tracking (last N durations for percentile calc)
        self._durations: Deque[float] = deque(maxlen=self.WINDOW_SIZE)
        
        # Error tracking
        self._error_counts: Dict[str, int] = {}
        
    def stream_started(self, session_id: str) -> None:
        """Record a stream starting."""
        with self._lock:
            self._streams_total += 1
            metrics = StreamMetrics(
                session_id=session_id,
                start_time=time.time(),
            )
            self._active_streams[session_id] = metrics
            log.debug("metric_stream_started", session_id=session_id)
    
    def stream_status_changed(self, session_id: str, status: str) -> None:
        """Record a stream status change."""
        with self._lock:
            if session_id in self._active_streams:
                self._active_streams[session_id].status_history.append(status)
    
    def stream_completed(self, session_id: str, success: bool, error_code: Optional[str] = None) -> None:
        """Record a stream completing."""
        with self._lock:
            metrics = self._active_streams.pop(session_id, None)
            if metrics is None:
                # Stream we didn't track the start of
                metrics = StreamMetrics(
                    session_id=session_id,
                    start_time=time.time(),
                )
            
            metrics.end_time = time.time()
            metrics.success = success
            metrics.error_code = error_code
            
            if success:
                self._streams_success += 1
            else:
                self._streams_failed += 1
                if error_code:
                    self._error_counts[error_code] = self._error_counts.get(error_code, 0) + 1
            
            # Record duration
            if metrics.duration_seconds is not None:
                self._durations.append(metrics.duration_seconds)
            
            # Add to rolling window
            self._recent_streams.append(metrics)
            
            log.debug(
                "metric_stream_completed",
                session_id=session_id,
                success=success,
                duration=metrics.duration_seconds,
                error_code=error_code,
            )
    
    def get_active_count(self) -> int:
        """Get count of currently active streams."""
        with self._lock:
            return len(self._active_streams)
    
    def get_stats(self) -> Dict:
        """Get current metrics snapshot."""
        with self._lock:
            uptime = time.time() - self._start_time
            
            # Calculate success rate
            completed = self._streams_success + self._streams_failed
            success_rate = (self._streams_success / completed * 100) if completed > 0 else 0.0
            
            # Calculate latency percentiles
            durations = sorted(self._durations)
            p50 = self._percentile(durations, 50)
            p95 = self._percentile(durations, 95)
            p99 = self._percentile(durations, 99)
            avg = sum(durations) / len(durations) if durations else 0
            
            return {
                "uptime_seconds": round(uptime, 2),
                "streams": {
                    "total": self._streams_total,
                    "active": len(self._active_streams),
                    "success": self._streams_success,
                    "failed": self._streams_failed,
                    "success_rate_percent": round(success_rate, 2),
                },
                "latency_seconds": {
                    "avg": round(avg, 3),
                    "p50": round(p50, 3) if p50 else None,
                    "p95": round(p95, 3) if p95 else None,
                    "p99": round(p99, 3) if p99 else None,
                },
                "errors": dict(self._error_counts),
                "active_sessions": list(self._active_streams.keys()),
            }
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> Optional[float]:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return None
        k = (len(sorted_data) - 1) * percentile / 100
        f = int(k)
        c = f + 1 if f + 1 < len(sorted_data) else f
        return sorted_data[f] + (sorted_data[c] - sorted_data[f]) * (k - f)
    
    def to_prometheus(self) -> str:
        """Export metrics in Prometheus text format."""
        stats = self.get_stats()
        lines = []
        
        # Help and type declarations
        lines.append("# HELP jamie_uptime_seconds Time since service started")
        lines.append("# TYPE jamie_uptime_seconds gauge")
        lines.append(f"jamie_uptime_seconds {stats['uptime_seconds']}")
        
        lines.append("")
        lines.append("# HELP jamie_streams_total Total number of streams started")
        lines.append("# TYPE jamie_streams_total counter")
        lines.append(f"jamie_streams_total {stats['streams']['total']}")
        
        lines.append("")
        lines.append("# HELP jamie_streams_active Currently active streams")
        lines.append("# TYPE jamie_streams_active gauge")
        lines.append(f"jamie_streams_active {stats['streams']['active']}")
        
        lines.append("")
        lines.append("# HELP jamie_streams_success_total Successful streams")
        lines.append("# TYPE jamie_streams_success_total counter")
        lines.append(f"jamie_streams_success_total {stats['streams']['success']}")
        
        lines.append("")
        lines.append("# HELP jamie_streams_failed_total Failed streams")
        lines.append("# TYPE jamie_streams_failed_total counter")
        lines.append(f"jamie_streams_failed_total {stats['streams']['failed']}")
        
        # Latency histogram-style metrics
        lines.append("")
        lines.append("# HELP jamie_stream_duration_seconds Stream duration")
        lines.append("# TYPE jamie_stream_duration_seconds summary")
        latency = stats['latency_seconds']
        if latency['p50'] is not None:
            lines.append(f'jamie_stream_duration_seconds{{quantile="0.5"}} {latency["p50"]}')
        if latency['p95'] is not None:
            lines.append(f'jamie_stream_duration_seconds{{quantile="0.95"}} {latency["p95"]}')
        if latency['p99'] is not None:
            lines.append(f'jamie_stream_duration_seconds{{quantile="0.99"}} {latency["p99"]}')
        
        # Error counts by code
        if stats['errors']:
            lines.append("")
            lines.append("# HELP jamie_errors_total Errors by code")
            lines.append("# TYPE jamie_errors_total counter")
            for code, count in stats['errors'].items():
                lines.append(f'jamie_errors_total{{code="{code}"}} {count}')
        
        return "\n".join(lines) + "\n"


# Global metrics instance
_metrics: Optional[MetricsCollector] = None


def get_metrics() -> MetricsCollector:
    """Get or create the global metrics collector."""
    global _metrics
    if _metrics is None:
        _metrics = MetricsCollector()
    return _metrics


def reset_metrics() -> None:
    """Reset metrics (for testing)."""
    global _metrics
    _metrics = MetricsCollector()
