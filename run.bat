@echo off
echo ========================================
echo   Sistema de Geracao de PDF com Excel
echo ========================================
echo.
echo Instalando dependencias...
pip install -r requirements.txt
echo.
echo Criando arquivo de exemplo...
python criar_exemplo.py
echo.
echo Iniciando o sistema...
echo Acesse: http://localhost:5000
echo.
python app.py
pause 