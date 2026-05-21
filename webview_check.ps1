# WebView Checker - PowerShell Wrapper
# Usage: .\webview_check.ps1 <apk_file> [options]

param(
    [Parameter(Mandatory=$true, Position=0)]
    [string]$ApkFile,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Arguments
)

# Validate APK file
if (-not (Test-Path $ApkFile)) {
    Write-Error "APK file not found: $ApkFile"
    exit 1
}

# Initialize variables
$script = "check_webview.py"
$args = @($ApkFile)

# Parse arguments
$i = 0
while ($i -lt $Arguments.Count) {
    $arg = $Arguments[$i]
    
    switch ($arg) {
        "-advanced" {
            $script = "check_webview_advanced.py"
        }
        "-json" {
            $args += "--json"
        }
        "-verbose" {
            $args += "-v"
        }
        "-output" {
            if ($i + 1 -lt $Arguments.Count) {
                $args += "-o"
                $args += $Arguments[$i + 1]
                $i++
            }
        }
        "-help" {
            Show-Usage
            exit 0
        }
        default {
            $args += $arg
        }
    }
    
    $i++
}

# Show usage information
function Show-Usage {
    Write-Host ""
    Write-Host "WebView Checker - PowerShell Wrapper"
    Write-Host ""
    Write-Host "Usage: .\webview_check.ps1 <apk_file> [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -advanced     Use advanced analysis with decompilation"
    Write-Host "  -json         Output in JSON format"
    Write-Host "  -verbose      Enable verbose output"
    Write-Host "  -output FILE  Save report to file"
    Write-Host "  -help         Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\webview_check.ps1 app.apk"
    Write-Host "  .\webview_check.ps1 app.apk -advanced"
    Write-Host "  .\webview_check.ps1 app.apk -json -output report.json"
    Write-Host ""
}

# Run the analysis
Write-Host ""
Write-Host "[*] Running WebView analysis with $script..."
Write-Host ""

& python $script @args

if ($LASTEXITCODE -ne 0) {
    Write-Error "Analysis failed with exit code: $LASTEXITCODE"
    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "[+] Analysis completed successfully!"
