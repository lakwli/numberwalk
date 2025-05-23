@echo off
setlocal enabledelayedexpansion

::######################################
:: DynaRetire Deployment Script (Windows)
::######################################
:: STEP 1: Set these environment variables if needed!
::
:: Optional (shown with defaults):
::   set DOCKER_PORT=5000       # App will be at localhost:5000
::   set DEPLOY_NAME=numberwalk # Container name (affects log directory)
::   set LOG_DIR=C:\logs       # Where to store logs on your host machine
::
:: Example deployment:
::   set DOCKER_PORT=8080
::   set DEPLOY_NAME=myapp
::   set LOG_DIR=D:\logs
::   
::   deploy_script.bat
::
:: This will:
:: 1. Deploy container named 'myapp'
:: 2. Make app available at http://localhost:8080
:: 3. Write logs to your host machine at D:\logs\myapp\
::    - You can read these logs directly with: type D:\logs\myapp\app.log
::    - No need to enter the container to view logs
::######################################

:: Settings
set IMAGE_NAME=ghcr.io/lakwli/numberwalk:latest
if "%DEPLOY_NAME%"=="" set DEPLOY_NAME=numberwalk
if "%DOCKER_PORT%"=="" set DOCKER_PORT=5000
if "%LOG_DIR%"=="" set LOG_DIR=C:\logs

set HOST_LOGS=%LOG_DIR%\%DEPLOY_NAME%

:: Create logs directory
echo Setting up logs directory at: %HOST_LOGS%
if not exist "%HOST_LOGS%" mkdir "%HOST_LOGS%"

:: Clean up old container
echo Cleaning up old container...
docker rm -f %DEPLOY_NAME% 2>nul
docker rmi -f %IMAGE_NAME% 2>nul

:: Pull latest image
echo Pulling the latest image...
docker pull %IMAGE_NAME%

if errorlevel 1 (
    echo Failed to pull Docker image. Exiting.
    exit /b 1
)

:: Start container with project-specific log volume
echo Starting container '%DEPLOY_NAME%' using image %IMAGE_NAME%...
docker run -d ^
    --name %DEPLOY_NAME% ^
    -p "%DOCKER_PORT%:5000" ^
    -v "%HOST_LOGS%:/app/logs" ^
    %IMAGE_NAME%

if errorlevel 1 (
    echo Failed to start container. Exiting.
    exit /b 1
) else (
    echo Container %DEPLOY_NAME% started successfully!
    echo.
    echo Your logs are directly accessible on the host machine at:
    echo   %HOST_LOGS%\
    echo.
    echo You can view them with regular commands (no need to use docker^):
    echo   type %HOST_LOGS%\app.log    # View application logs
    echo   type %HOST_LOGS%\error.log  # View error logs
    echo   findstr "ERROR" "%HOST_LOGS%\*.log"  # Search for errors in all logs
    echo.
    echo Note: The logs are stored on your host machine, not just in the container.
    echo       You can use any standard Windows tools to read, search, and analyze them.
)
