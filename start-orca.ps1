param (
    [switch]$Live
)

$MODE = if ($Live) { "LIVE" } else { "DEMO" }
Write-Host "Starting ORCA Master Controller in $MODE mode..."

# Pass the mode as an environment variable to the Python backend
$env:ORCA_MODE = $MODE

# Launch the FastAPI backend
python -m uvicorn backend.main:app --reload --port 8000