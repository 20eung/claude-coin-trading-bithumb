"""
로컬 SQLite 데이터베이스 모듈

Supabase PostgreSQL → SQLite 로컬 마이그레이션용
PostgREST API 호출 대신 로컬 파일 기반 쿼리 실행
"""

import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

KST = timezone(timedelta(hours=9))
DB_DIR = Path(__file__).parent
DB_PATH = DB_DIR / "trading.db"


def _kst_now() -> str:
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S+09:00")


def _uuid() -> str:
    return str(uuid.uuid4())


@contextmanager
def get_db():
    """DB 커넥션 컨텍스트 매니저"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """DB 초기화 (스키마 생성)"""
    schema_path = DB_DIR / "schema.sql"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = f.read()

    with get_db() as conn:
        conn.executescript(schema)


def init_db_if_not_exists():
    """DB 파일이 없으면 초기화"""
    if not DB_PATH.exists():
        init_db()


# ── decisions ──────────────────────────────────────────────

def insert_decision(
    decision: str,
    reason: str,
    market: str = "KRW-BTC",
    confidence: float = None,
    market_data_snapshot: str = None,
    fear_greed_value: int = None,
    rsi_value: float = None,
    current_price: int = None,
    sma20_price: int = None,
    trade_amount: int = None,
    trade_volume: float = None,
    executed: bool = False,
    execution_result: dict = None,
    profit_loss: float = None,
) -> str:
    """매매 결정 기록 저장"""
    decision_id = _uuid()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO decisions
            (id, market, decision, confidence, reason, market_data_snapshot,
             fear_greed_value, rsi_value, current_price, sma20_price,
             trade_amount, trade_volume, executed, execution_result, profit_loss)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                decision_id, market, decision, confidence, reason,
                market_data_snapshot, fear_greed_value, rsi_value,
                current_price, sma20_price, trade_amount, trade_volume,
                int(executed), json.dumps(execution_result) if execution_result else None,
                profit_loss
            )
        )
    return decision_id


def get_recent_decisions(limit: int = 10) -> list:
    """최근 매매 결정 조회"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM decisions ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def update_decision_executed(decision_id: str, executed: bool, execution_result: dict = None, profit_loss: float = None):
    """결정 실행 결과 업데이트"""
    with get_db() as conn:
        conn.execute(
            "UPDATE decisions SET executed = ?, execution_result = ?, profit_loss = ? WHERE id = ?",
            (int(executed), json.dumps(execution_result) if execution_result else None, profit_loss, decision_id)
        )


# ── portfolio_snapshots ────────────────────────────────────

def insert_portfolio_snapshot(
    total_krw: int,
    total_crypto_value: int,
    total_value: int,
    holdings: list,
    daily_return: float = None,
    cumulative_return: float = None,
) -> str:
    """포트폴리오 스냅샷 저장"""
    snapshot_id = _uuid()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO portfolio_snapshots
            (id, total_krw, total_crypto_value, total_value, holdings, daily_return, cumulative_return)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (snapshot_id, total_krw, total_crypto_value, total_value, json.dumps(holdings), daily_return, cumulative_return)
        )
    return snapshot_id


def get_recent_portfolio_snapshots(limit: int = 10) -> list:
    """최근 포트폴리오 스냅샷 조회"""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM portfolio_snapshots ORDER BY created_at DESC LIMIT ?",
            (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


# ── market_data ────────────────────────────────────────────

def insert_market_data(
    market: str,
    price: int,
    volume_24h: float = None,
    change_rate_24h: float = None,
    fear_greed_value: int = None,
    fear_greed_class: str = None,
    rsi_14: float = None,
    sma_20: int = None,
    news_sentiment: str = None,
) -> str:
    """시장 데이터 기록 저장"""
    data_id = _uuid()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO market_data
            (id, market, price, volume_24h, change_rate_24h, fear_greed_value,
             fear_greed_class, rsi_14, sma_20, news_sentiment)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (data_id, market, price, volume_24h, change_rate_24h,
             fear_greed_value, fear_greed_class, rsi_14, sma_20, news_sentiment)
        )
    return data_id


# ── feedback ────────────────────────────────────────────────

def insert_feedback(
    feedback_type: str,
    content: str,
    expires_at: datetime = None,
) -> str:
    """피드백 저장"""
    feedback_id = _uuid()
    expires_str = expires_at.isoformat() if expires_at else None
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO feedback (id, type, content, expires_at)
            VALUES (?, ?, ?, ?)
            """,
            (feedback_id, feedback_type, content, expires_str)
        )
    return feedback_id


def get_pending_feedback() -> list:
    """미반영 피드백 조회"""
    now = _kst_now()
    with get_db() as conn:
        rows = conn.execute(
            """
            SELECT * FROM feedback
            WHERE applied = 0 AND (expires_at IS NULL OR expires_at > ?)
            ORDER BY created_at DESC
            """,
            (now,)
        ).fetchall()
    return [dict(row) for row in rows]


def mark_feedback_applied(feedback_id: str):
    """피드백 적용 완료 처리"""
    with get_db() as conn:
        conn.execute(
            "UPDATE feedback SET applied = 1, applied_at = ? WHERE id = ?",
            (_kst_now(), feedback_id)
        )


# ── execution_logs ─────────────────────────────────────────

def insert_execution_log(
    execution_mode: str,
    decision_id: str = None,
    duration_ms: int = None,
    data_sources: dict = None,
    errors: list = None,
    raw_output: str = None,
) -> str:
    """실행 로그 저장"""
    log_id = _uuid()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO execution_logs
            (id, execution_mode, decision_id, duration_ms, data_sources, errors, raw_output)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (log_id, execution_mode, decision_id, duration_ms,
             json.dumps(data_sources) if data_sources else None,
             json.dumps(errors) if errors else None, raw_output)
        )
    return log_id


# ── strategy_history ───────────────────────────────────────

def insert_strategy_history(
    version: int,
    content: str,
    change_summary: str = None,
    changed_by: str = "user",
) -> str:
    """전략 변경 이력 저장"""
    history_id = _uuid()
    with get_db() as conn:
        conn.execute(
            """
            INSERT INTO strategy_history (id, version, content, change_summary, changed_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (history_id, version, content, change_summary, changed_by)
        )
    return history_id


def get_latest_strategy_version() -> int:
    """최신 전략 버전 번호 조회"""
    with get_db() as conn:
        row = conn.execute(
            "SELECT MAX(version) as max_ver FROM strategy_history"
        ).fetchone()
    return row["max_ver"] or 0
