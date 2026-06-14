# 修复 Android Cleartext 配置（允许 HTTP）
# 在 npx cap sync 后执行此脚本

$manifestPath = "android/app/src/main/AndroidManifest.xml"

if (Test-Path $manifestPath) {
    $content = Get-Content $manifestPath -Raw
    
    if ($content -notmatch 'android:usesCleartextTraffic') {
        $content = $content -replace 'android:theme="@style/AppTheme">', 'android:theme="@style/AppTheme"' + "`n" + '        android:usesCleartextTraffic="true">'
        $content | Out-File $manifestPath -Encoding UTF8
        Write-Host "✅ 已添加 android:usesCleartextTraffic='true'" -ForegroundColor Green
    } else {
        Write-Host "✅ Cleartext 配置已存在" -ForegroundColor Green
    }
} else {
    Write-Host "❌ 未找到 AndroidManifest.xml，请先执行 npx cap sync" -ForegroundColor Red
}
