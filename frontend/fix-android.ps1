# Simple script to fix Android Cleartext
$manifestPath = "android/app/src/main/AndroidManifest.xml"

if (Test-Path $manifestPath) {
    $content = Get-Content $manifestPath -Raw
    
    if ($content -notmatch 'usesCleartextTraffic') {
        $content = $content -replace 'android:theme="@style/AppTheme">', 'android:theme="@style/AppTheme"`n        android:usesCleartextTraffic="true">'
        $content | Out-File $manifestPath -Encoding UTF8
        Write-Host "OK: Added usesCleartextTraffic" -ForegroundColor Green
    } else {
        Write-Host "OK: Already configured" -ForegroundColor Green
    }
} else {
    Write-Host "ERROR: AndroidManifest.xml not found" -ForegroundColor Red
}
