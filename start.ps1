param (
    [string]$mode = "background"
)

# Function to start the Express API in the background
function Start-Express-Api-Bg {
    Write-Host "Starting Express API in the background..."
    Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "cd express_API; npm install; npm start"
}

# Function to start the Flask API in the background
function Start-Flask-Api-Bg {
    Write-Host "Starting Flask API in the background..."
    Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "cd flask_API; .\start.ps1"
}

# Function to start the Express API in a new PowerShell window
function Start-Express-Api-Terminal {
    Write-Host "Starting Express API in a new PowerShell window..."
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd express_API; npm start"
}

# Function to start the Flask API in a new PowerShell window
function Start-Flask-Api-Terminal {
    Write-Host "Starting Flask API in a new PowerShell window..."
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "cd flask_API; .\start.ps1"
}

# Main script logic

if ($mode -eq "terminal") {
    Start-Express-Api-Terminal
    Start-Flask-Api-Terminal
} else {
    Start-Express-Api-Bg
    Start-Flask-Api-Bg
}
