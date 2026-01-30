@echo off
title CEVIZALTI - GitHub Yukleme

echo ===============================
echo  CEVIZALTI GITHUB YUKLEME
echo ===============================
echo.

cd /d C:\cevizalti-backend

echo Degisen dosyalar kontrol ediliyor...
git status

echo.
echo GitHub'dan guncel durum aliniyor...
git pull origin main

echo.
echo Dosyalar GitHub'a yukleniyor...
git add .

git commit -m "Update version.json ve python dosyalari"

git push origin main

echo.
echo ✔ Yukleme tamamlandi
pause
