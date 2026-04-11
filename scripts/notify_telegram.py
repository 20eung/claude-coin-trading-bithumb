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

# FGI 분류 한국어 매핑
FGI_CLASS_KO = {
    "Extreme Fear": "극도공포",
    "Fear": "공포",
    "Neutral": "중립",
    "Greed": "탐욕",
    "Extreme Greed": "극도탐욕",
}

DECISION_EMOJI = {
    "매수": "\U0001f4c8",      # 📈
    "매도": "\U0001f4c9",      # 📉
    "관망": "\u23f8\ufe0f",    # ⏸️
}

KST = timezone(timedelta(hours=9))


def _get_credentials():
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or os.environ.get("TELEGRAM_USER_ID")
    if not bot_token or not chat_id:
        raise RuntimeError("TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID 미설정")
    thread_id = os.environ.get("TELEGRAM_THREAD_ID")
    return bot_token, chat_id, thread_id


def _send(bot_token: str, chat_id: str, text: str, parse_mode: str = None, thread_id: str = None):
    payload = {"chat_id": chat_id, "text": text}
    if parse_mode:
        payload["parse_mode"] = parse_mode
    if thread_id:
        payload["message_thread_id"] = int(thread_id)

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
    bot_token, chat_id, thread_id = _get_credentials()

    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    emoji = EMOJI.get(msg_type, "\U0001f4ac")
    text = f"{emoji} <b>{html.escape(title)}</b>\n\n{html.escape(body)}\n\n<i>{html.escape(ts)}</i>"

    _send(bot_token, chat_id, text, parse_mode="HTML", thread_id=thread_id)
    return {"success": True, "type": msg_type, "title": title}


def send_report(data):
    """분석 리포트를 구조화된 포맷으로 전송 (HTML)"""
    bot_token, chat_id, thread_id = _get_credentials()

    if isinstance(data, str):
        data = json.loads(data)

    ts = datetime.now(KST).strftime("%Y-%m-%d %H:%M KST")
    decision = data.get("decision", "관망")
    decision_en = data.get("decision_en", "HOLD")
    d_emoji = DECISION_EMOJI.get(decision, "\u23f8\ufe0f")
    e = html.escape

    lines = [
        f"\U0001f4b0 {d_emoji} <b>{e(decision)} ({e(decision_en)})</b>",
        ts,
    ]

    # 【시장 분석】
    market = data.get("market", {})
    if market:
        lines.append("")
        lines.append("<b>\u3010시장 분석\u3011</b>")

        # price
        price = market.get("current_price") or market.get("price")
        if price:
            price_str = f"{int(price):,}" if isinstance(price, (int, float)) else str(price)
            lines.append(f"- 현재가: {e(price_str)}원")

        # SMA(20)
        sma20 = market.get("sma_20") or market.get("sma20")
        if sma20:
            sma_str = f"{int(sma20):,}" if isinstance(sma20, (int, float)) else str(sma20)
            pct = market.get("price_vs_sma20_pct")
            if pct is not None:
                lines.append(f"- SMA(20): {e(sma_str)}원 ({e(str(pct))}%)")
            else:
                lines.append(f"- SMA(20): {e(sma_str)}원")

        # RSI
        rsi = market.get("rsi_14") or market.get("rsi")
        if rsi:
            lines.append(f"- RSI: {e(str(rsi))}")

        # FGI
        fgi_val = market.get("fgi") or market.get("fear_greed_value")
        fgi_cls = market.get("fgi_classification") or market.get("fear_greed_class") or ""
        if fgi_val:
            fgi_ko = FGI_CLASS_KO.get(fgi_cls, fgi_cls) if fgi_cls else ""
            if fgi_ko:
                lines.append(f"- FGI: {e(str(fgi_val))} ({e(fgi_ko)})")
            else:
                lines.append(f"- FGI: {e(str(fgi_val))}")

    # 【결정 근거】
    reasons = data.get("reasons", []) or data.get("reasons_detail", [])
    if reasons:
        lines.append("")
        lines.append("<b>\u3010결정 근거\u3011</b>")
        for reason in reasons:
            lines.append(f"- {e(str(reason))}")

    # 【포트폴리오】
    portfolio = data.get("portfolio", {})
    if portfolio:
        lines.append("")
        lines.append("<b>\u3010포트폴리오\u3011</b>")

        # 보유수량
        btc = portfolio.get("btc_holdings") or portfolio.get("holdings")
        if btc:
            lines.append(f"- 보유수량: {e(str(btc))} BTC")

        # 평가금액
        eval_amt = portfolio.get("eval_amount")
        if eval_amt:
            eval_str = f"{float(eval_amt):,.0f}" if isinstance(eval_amt, (int, float)) else str(eval_amt)
            lines.append(f"- 평가금액: {e(eval_str)} 원")

        # 평가손익
        pl = portfolio.get("profit_loss_pct") or portfolio.get("profit_loss")
        if pl:
            if isinstance(pl, (int, float)):
                sign = "+" if pl > 0 else ""
                lines.append(f"- 평가손익: {e(sign)}{e(str(pl))}%")
            else:
                lines.append(f"- 평가손익: {e(str(pl))}")

    text = "\n".join(lines)
    _send(bot_token, chat_id, text, parse_mode="HTML", thread_id=thread_id)
    return {"success": True, "type": "report", "decision": decision}


def send_photo(image_path: str, caption: str):
    """이미지(차트) 전송"""
    bot_token, chat_id, thread_id = _get_credentials()

    data = {"chat_id": chat_id, "caption": caption}
    if thread_id:
        data["message_thread_id"] = int(thread_id)

    with open(image_path, "rb") as f:
        r = requests.post(
            f"{TELEGRAM_API.format(token=bot_token)}/sendPhoto",
            data=data,
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
