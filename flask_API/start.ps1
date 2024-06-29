# Function to check if the virtual environment is activated
function Is-VenvActivated {
    return $env:VIRTUAL_ENV -ne $null
}

# Function to create and activate the virtual environment on Windows
function Create-And-Activate-Venv-Windows {
    Write-Host "Setting up virtual environment..."
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
}

# Function to create and activate the virtual environment on Unix-like systems
function Create-And-Activate-Venv-Unix {
    Write-Host "Setting up virtual environment..."
    python -m venv venv
    . ./venv/bin/activate
}

# Function to activate the virtual environment on Windows
function Activate-Venv-Windows {
    & .\venv\Scripts\Activate.ps1
}

# Function to activate the virtual environment on Unix-like systems
function Activate-Venv-Unix {
    . ./venv/bin/activate
}

# Function to check if the virtual environment directory exists
function Is-VenvDirectoryPresent {
    return Test-Path -Path "./venv"
}

# Function to install dependencies if needed
function Install-Dependencies {
    Write-Host "Installing dependencies..."
    pip install -r requirements.txt --quiet --ignore-installed
    python -m spacy download en_core_web_sm --quiet
}

# Function to check if all dependencies from requirements.txt are installed
function Are-DependenciesInstalled {
    $requirements = Get-Content -Path "requirements.txt"
    foreach ($requirement in $requirements) {
        if (-not (pip show $requirement)) {
            return $false
        }
    }
    return $true
}

# Function to check if the .env file exists
function Is-EnvFilePresent {
    return Test-Path -Path ".env"
}

# Main script logic

# Determine the correct activation function based on the operating system
$IsWindows = $false
if ($env:OS -eq "Windows_NT") {
    $IsWindows = $true
}

if (Is-VenvDirectoryPresent) {
    # Try to activate the existing virtual environment
    if ($IsWindows) {
        Activate-Venv-Windows
    } else {
        Activate-Venv-Unix
    }
} else {
    # Create and activate the virtual environment
    if ($IsWindows) {
        Create-And-Activate-Venv-Windows
    } else {
        Create-And-Activate-Venv-Unix
    }
}

# Check if virtual environment is activated
if (-not (Is-VenvActivated)) {
    Write-Host "Virtual environment is not activated. Exiting."
    exit 1
}

# Install dependencies if they are not already installed
if (-not (Are-DependenciesInstalled)) {
    Install-Dependencies
}

# Check if the .env file exists and create it if it doesn't
if (-not (Is-EnvFilePresent)) {
    Write-Host "Creating .env file..."
    New-Item -ItemType File -Path .env
    Add-Content -Path .env -Value "DATABASE_URL=sqlite:///./test.db"
    Add-Content -Path .env -Value "EXPRESS_SERVER_ADDRESS= http://localhost:3000"
    Add-Content -Path .env -Value "EXPRESS_SERVER_EMAIL = email@example.com"
    Add-Content -Path .env -Value "EXPRESS_SERVER_PASSWORD = password"
}

# Determine the current python environment
python -c "import sys; print(sys.executable)"

# Check if flask-socketio is installed
pip show flask-socketio > $null
if ($LASTEXITCODE -eq 0) {
    Write-Host "flask-socketio is installed."
} else {
    Write-Host "flask-socketio is not installed."
}

# Start the Flask application
Write-Host "Starting Flask application..."
Start-Process -NoNewWindow -FilePath "powershell" -ArgumentList "-Command", "uvicorn app.main:app --host 0.0.0.0 --port 5000"


# Run topics_population.py in a new terminal
Write-Host "Running topics_population.py in a new terminal..."
if ($IsWindows) {
    Start-Process -FilePath "powershell" -ArgumentList "-NoExit", "-Command", "python models\HireUp_Question_Generation\topics_population.py; if ($LASTEXITCODE -ne 0) { pause }"
} else {
    Start-Process -FilePath "bash" -ArgumentList "-c", "source ./venv/bin/activate && python models\HireUp_Question_Generation\topics_population.py; read -p 'Press [Enter] key to continue...'"
}