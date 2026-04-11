# Claude 암호화폐 자동매매 봇

Claude Code가 직접 데이터를 수집하고, 분석하고, 판단하고, 매매까지 실행하는 AI 트레이딩 시스템입니다.

> **원본 프로젝트:** [Dante Labs - claude-coin-trading](https://github.com/dandacompany/claude-coin-trading) (Upbit API)
>
> 이 프로젝트는 원본 Upbit 버전을 Bithumb 거래소로 마이그레이션한 Fork입니다.

## 핵심 기능

- **자동 거래**: Bithumb 거래소 REST API 연동
- **자연어 전략**: `strategy.md`에 전략을 자연어로 정의하면 Claude가 해석
- **기술적 분석**: RSI, SMA, MACD, 볼린저밴드, 스토캐스틱
- **시장 심리**: Fear & Greed Index + 뉴스 감성 분석
- **자동 실행**: cron 스케줄링 (8시간 간격)
- **알림**: Telegram Bot으로 실시간 알림

## 빠른 시작

```bash
# 프로젝트 클론
git clone https://github.com/20eung/claude-coin-trading-bithumb.git
cd claude-coin-trading-bithumb

# 환경 설정
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# .env 파일에 API 키 설정
# - BITHUMB_ACCESS_KEY, BITHUMB_SECRET_KEY (Bithumb)
# - TAVILY_API_KEY (뉴스)
# - TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID (알림)

# 데이터베이스 초기화
python3 -c "from database.db import init_db_if_not_exists; init_db_if_not_exists()"

# 수동 분석 실행
bash scripts/run_analysis.sh

# cron 등록 (8시간 간격)
bash scripts/setup_cron.sh install
```

## 프로젝트 구조

```
.
├── CLAUDE.md                 # 프로젝트 지침
├── strategy.md               # 매매 전략 (자연어)
├── database/
│   ├── schema.sql           # SQLite 스키마
│   └── db.py                # DB 모듈
├── scripts/
│   ├── collect_market_data.py   # 시세 + 기술지표
│   ├── collect_fear_greed.py    # 공포탐욕지수
│   ├── collect_news.py          # 뉴스 수집
│   ├── capture_chart.py         # 차트 캡처
│   ├── get_portfolio.py        # 포트폴리오 조회
│   ├── execute_trade.py       # 매매 실행
│   ├── notify_telegram.py     # Telegram 알림
│   ├── run_analysis.sh        # 분석 파이프라인
│   ├── cron_run.sh            # cron 래퍼
│   └── setup_cron.sh         # cron 등록
└── data/
    ├── charts/               # 캡처된 차트
    └── snapshots/            # 실행 시점 데이터
```

## 안전장치

| 파라미터 | 기본값 | 설명 |
|----------|--------|------|
| `DRY_RUN` | `true` | 분석만 수행, 실제 매매 없음 |
| `MAX_TRADE_AMOUNT` | `100,000 KRW` | 1회 매매 상한 |
| `EMERGENCY_STOP` | `false` | `true` 설정 시 모든 매매 중지 |

**실제 거래 전 반드시 `DRY_RUN=false`로 변경하고 충분히 테스트하세요.**

## 실행 모드

### 대화형 (Claude 세션)

```bash
claude
```

### 자동 실행 (cron)

```bash
bash scripts/setup_cron.sh install    # 등록
bash scripts/setup_cron.sh status     # 상태 확인
bash scripts/setup_cron.sh remove     # 해제
```

## 라이선스

MIT
