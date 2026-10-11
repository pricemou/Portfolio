@echo off
cd /d "%~dp0.."
echo === STATUS ===
git status
echo === BRANCH ===
git branch -vv
echo === LOG ===
git log -8 --oneline
echo === DIFF STAT ===
git diff --stat
git diff --staged --stat
echo === UNTRACKED ===
git status -u --porcelain
