@echo off
chcp 65001 >nul
REM ============================================================
REM  FinPath - Opus 4.8 phan tich tin (thay Claude API).
REM  Chay moi sang: xuat tin tho -> claude headless ghi ai_digest.json
REM  -> merge vao news.json -> push. Dung goi Claude Code (khong ton API).
REM ============================================================
cd /d "C:\Users\chuta\finpath-personal"

REM 1) Xuat tin RSS tho cho Opus doc
python updater\update_news.py --rawdump

REM 2) Opus phan tich + ghi ai_digest.json (chi cho phep sua file, khong chay lenh)
type updater\ai_prompt.txt | "C:\Users\chuta\AppData\Roaming\npm\claude.cmd" -p --permission-mode acceptEdits

REM 3) Merge digest vao news.json
python updater\update_news.py

REM 4) Day len GitHub
git add docs/data/ai_digest.json docs/data/news.json
git commit -m "Tin AI: Opus tu dong"
git fetch origin
git rebase -X theirs origin/main
git push

echo Done %date% %time%
