@echo off
echo ========================================
echo   ENOVACOM SmartReport - Demarrage
echo ========================================
echo.

setlocal enabledelayedexpansion

REM Vérifier si Python est installé
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    echo Veuillez installer Python 3.8+ depuis https://python.org
    pause
    exit /b 1
)

REM Créer l'environnement virtuel si il n'existe pas
if not exist venv (
    echo Creation de l'environnement virtuel...
    python -m venv venv
    if errorlevel 1 (
        echo ERREUR: Impossible de creer l'environnement virtuel
        pause
        exit /b 1
    )
)

REM Activer l'environnement virtuel
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERREUR: Impossible d'activer l'environnement virtuel
    pause
    exit /b 1
)

REM Mettre à jour pip
echo Mise a jour de pip...
python -m pip install --upgrade pip --quiet

REM Installer les dépendances
echo Installation/Verification des dependances...
echo (Flask, ReportLab, svglib, BeautifulSoup4, python-docx, etc.)
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo ERREUR: Impossible d'installer les dependances
    echo Verifiez votre connexion internet et reessayez
    pause
    exit /b 1
)
echo.
echo Toutes les dependances sont installees !

REM Créer le fichier .env s'il n'existe pas
if not exist .env (
    echo Creation du fichier .env...
    copy .env.example .env >nul
    echo ATTENTION: Editez le fichier .env pour configurer vos cles API
)

echo.
echo ========================================
echo    Demarrage du serveur...
echo ========================================
echo.
echo Interface disponible sur: http://127.0.0.1:5173
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

REM Démarrer l'application
python app.py

echo.
echo Serveur arrete.
pause