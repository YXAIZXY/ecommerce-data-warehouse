@echo off
chcp 65001 >nul
cd /d C:\Users\Administrator\Desktop\ecommerce-data-warehouse

echo [1/4] Generating data...
python -X utf8 scripts\01_generate_data.py
echo.
echo [2/4] Resetting database...
del /q data\warehouse.duckdb 2>nul
echo [3/4] Creating tables + running ETL...
python -X utf8 scripts\02_create_tables.py
python -X utf8 scripts\07_scheduler.py
echo.
echo [4/4] Generating report...
python -X utf8 scripts\08_report.py

echo.
echo ============ DONE ============
echo Report: output\report.md
echo Chart:  output\charts.png
pause
