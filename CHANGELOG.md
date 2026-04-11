# Changelog

## [1.2.0] - 2026-04-11

### 데이터베이스 로컬 SQLite 마이그레이션

Supabase PostgreSQL에서 로컬 SQLite로 데이터베이스를 변경했습니다.

- `database/schema.sql` - SQLite 스키마 (6개 테이블)
- `database/db.py` - CRUD 모듈
- `scripts/run_analysis.sh` - Supabase API → SQLite 조회로 변경
- **자동 초기화:** DB 파일이 없으면 자동 생성

### 텔레그램 리포트 포맷 개선

- FGI 분류를 한국어로 표시 (Extreme Fear → 극도공포)
- market, portfolio 필드를 구조화하여 가독성 향상

### 데이터 정리 로직 추가

- `run_analysis.sh`에 자동 정리 (snapshots: 30일, charts: 7일, logs: 30일)

### 문서 및 기타

- `.gitignore`에 `data/` 추가
- `docs/releases/`에 버전별 릴리즈 노트 추가

## [1.1.0] - 2026-03-04

### cron 자동화 및 텔레그램 포맷 개선

- `cron_run.sh` - Linux 환경 PATH 설정 추가
- `setup_cron.sh` - 대화형 간격 선택 지원
- `notify_telegram.py` - MarkdownV2 → HTML 전환, `report` JSON 타입 추가
- 텔레그램 그룹 topic (message_thread_id) 전송 지원

### 저장소 이름 변경

- GitHub 저장소명 `claude-coin-trading` → `claude-coin-trading-bithumb`

## [1.0.0] - 2026-03-03

### 거래소 마이그레이션: Upbit → Bithumb

거래소 API를 Upbit에서 Bithumb으로 전면 전환

## [0.1.0] - 2026-02-26

### 초기 릴리즈

- Claude Code 기반 암호화폐 자동매매 시스템
- Bithumb API 연동 (시세 조회, 포트폴리오, 매매 실행)
- Fear & Greed Index, Tavily 뉴스, Playwright 차트 캡처
- cron 자동화 파이프라인
- 6개 Claude 스킬 문서
