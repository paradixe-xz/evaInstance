# Fix Ollama daemon context issue
Write-Host "🔧 Fixing Ollama daemon context..."

# 1) Set environment variables for Ollama
$env:OLLAMA_MODELS = "C:\Users\herna\.ollama\models"
$env:OLLAMA_HOST = "http://localhost:11434"

# 2) Kill existing daemon
Write-Host "Stopping existing Ollama daemon..."
Get-Process -Name "ollama" -ErrorAction SilentlyContinue | Stop-Process -Force
Start-Sleep -Seconds 3

# 3) Start new daemon with correct context
Write-Host "Starting Ollama daemon with correct context..."
Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
Start-Sleep -Seconds 5

# 4) Verify models are now visible via HTTP API
Write-Host "Checking models via HTTP API..."
try {
    $response = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -TimeoutSec 10
    $modelCount = $response.models.Count
    Write-Host "✅ HTTP API now sees $modelCount models"
    $response.models | ForEach-Object { Write-Host "  - $($_.name)" }
} catch {
    Write-Host "❌ HTTP API still not working: $_"
}

# 5) Test chat with a simple model
Write-Host "Testing chat functionality..."
try {
    $testPayload = @{
        model = "llama3.2:3b"
        messages = @(
            @{
                role = "user"
                content = "Hello, just testing"
            }
        )
        stream = $false
    } | ConvertTo-Json -Depth 3

    $chatResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/chat" -Method POST -Body $testPayload -ContentType "application/json" -TimeoutSec 30
    Write-Host "✅ Chat test successful: $($chatResponse.message.content.Substring(0, 50))..."
} catch {
    Write-Host "❌ Chat test failed: $_"
}

Write-Host "🎉 Ollama fix complete! Restart your backend now."
