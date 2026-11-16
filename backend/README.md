# Backend (Django)

## 실행 방법
bash
cd backend
python3 -m venv .venv
source .venv/bin/activate      # 윈도우: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # SECRET_KEY 값 채우기
python manage.py migrate
python manage.py runserver


## 브랜치 규칙
- develop에서 `feature/backend-기능명` 브랜치를 따서 작업
- 작업 후 develop으로 PR (승인 1명 필요)
- migration 파일은 반드시 커밋
