#!/usr/bin/env python3
"""
텔레그램 알림 전송 스크립트

메시지 타입: trade, analysis, error, status, report
포맷: HTML (trade/analysis/error/status), 일반 텍스트 (report)

사용법:
  python3 scripts/notify_telegram.py trade "BTC 매수 실행" "10만원 매수, RSI 28"
  python3 scripts/notify_telegram.py error "데이터 수집 실패" "Bithumb API 타임아웃"
  python3 scripts/notify_telegram.py report '{"decision":"관망", ...}'
  echo '{"decision":"관망", ...}' | python3 scripts/notify_telegram.py report -

출력: JSON (stdout)
"""

import html
import json
import os
import sys
from datetime import datetime, timezone, timedelta

import requests

TELEGRAM_API = "https://api.telegram.org/bot{token}"

EMOJI = {
    "trade": "\U0001f4b0",     # 💰
    "analysis": "\U0001f4ca",  # 📊
    "error": "\U0001f6a8",     # 🚨
    "status": "\U0001f4cb",    # 📋
}

DECISION_EMOJI = {
    "매수": "\U0001f4c8",      # 📈
    "매도": "\U0001f4c9",      # 📉
    "관망": "\u23f8\ufe0f",    # ⏸️
}

KST = timezone(timedelta(hours=9))


def _get_credentials():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    user_id = os.environ.get("TELEGRAM_USER_ID")
    if not bot_token or not user_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_USER_ID 미설정")
    return bot_token, user_id


def _send(bot_token: str, user_id: str, text: str, parse_mode: str = None):
    payload = {"chat_id": user_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode

    r = requests.post(
        f"{TELEGRAM_API.format(token=bot_token)}/sendMessage",
        json=payload,
        timeout=10,
    )
    if not r.ok:
        raise RuntimeError(f"텔레그램 전송 실패: {r.text}")
    return r


def send_message(msg_type: str, title: str, body: str):
    """일반 메시지 전송 (HTML 포맷)"""
    bot_token, user_id = _get_credentials()

    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    emoji = EMOJI.get(msg_type, "\U0001f4ac")
    text = f"{emoji} <b>{html.escape(title)}</b>\n\n{html.escape(body)}\n\n<i>{html.escape(ts)}</i>"

    _send(bot_token, user_id, text, parse_mode="HTML")
    return {"success": True, "type": msg_type, "title": title}


def send_report(data):
    """분석 리포트를 구조화된 포맷으로 전송 (일반 텍스트)"""
    bot_token, user_id = _get_credentials()

    if isinstance(data, str):
        data = json.loads(data)

    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    decision = data.get("decision", "관망")
    decision_en = data.get("decision_en", "HOLD")
    d_emoji = DECISION_EMOJI.get(decision, "\u23f8\ufe0f")

    lines = [f"\U0001f4b0 {d_emoji} {decision} ({decision_en}) - {ts}"]

    # 【시장 분석】
    market = data.get("market", {})
    if market:
        lines.append("")
        lines.append("\u3010시장 분석\u3011")
        for key, value in market.items():
            lines.append(str(value))

    # 【결정 근거】
    reasons = data.get("reasons", [])
    if reasons:
        lines.append("")
        lines.append("\u3010결정 근거\u3011")
        for reason in reasons:
            lines.append(f"- {reason}")

    # 【포트폴리오】
    portfolio = data.get("portfolio", {})
    if portfolio:
        lines.append("")
        lines.append("\u3010포트폴리오\u3011")
        for key, value in portfolio.items():
            lines.append(str(value))

    text = "\n".join(lines)
    _send(bot_token, user_id, text)
    return {"success": True, "type": "report", "decision": decision}


def send_photo(image_path: str, caption: str):
    """이미지(차트) 전송"""
    bot_token, user_id = _get_credentials()

    with open(image_path, "rb") as f:
        r = requests.post(
            f"{TELEGRAM_API.format(token=bot_token)}/sendPhoto",
            data={"chat_id": user_id, "caption": caption},
            files={"photo": ("chart.png", f, "image/png")},
            timeout=30,
        )

    if not r.ok:
        raise RuntimeError(f"텔레그램 이미지 전송 실패: {r.text}")

    return {"success": True, "type": "photo", "path": image_path}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(
            "사용법:\n"
            '  python3 notify_telegram.py [trade|analysis|error|status] "제목" "본문"\n'
            "  python3 notify_telegram.py report '{JSON}'\n"
            "  echo '{JSON}' | python3 notify_telegram.py report -",
            file=sys.stderr,
        )
        sys.exit(1)

    msg_type = sys.argv[1]

    try:
        if msg_type == "report":
            # report: JSON을 인자 또는 stdin으로 받음
            if len(sys.argv) >= 3 and sys.argv[2] != "-":
                raw = sys.argv[2]
            else:
                raw = sys.stdin.read()
            result = send_report(raw)
        else:
            # 기존 타입: trade, analysis, error, status
            if len(sys.argv) < 4:
                print(
                    f'사용법: python3 notify_telegram.py {msg_type} "제목" "본문"',
                    file=sys.stderr,
                )
                sys.exit(1)
            result = send_message(msg_type, sys.argv[2], sys.argv[3])

        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        json.dump({"error": str(e)}, sys.stderr, ensure_ascii=False)
        sys.exit(1)
