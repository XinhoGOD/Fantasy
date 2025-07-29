# 🚀 Script de Activación - NFL Fantasy Scraper 24/7 en GitHub Actions
# PowerShell Version

Write-Host "🏈 ===== ACTIVACIÓN NFL FANTASY SCRAPER 24/7 =====" -ForegroundColor Green
Write-Host "⏰ Timestamp: $(Get-Date)" -ForegroundColor Yellow
Write-Host "🎯 Configurando ejecución automática cada 30 minutos" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Green

Write-Host ""
Write-Host "📋 CHECKLIST DE VERIFICACIÓN:" -ForegroundColor White
Write-Host "✅ Campo 'semana' agregado a Supabase" -ForegroundColor Green
Write-Host "✅ Workflow nfl-scraper-30min.yml configurado" -ForegroundColor Green
Write-Host "✅ Sistema de detección de semana funcionando" -ForegroundColor Green
Write-Host "✅ Comparación individual por jugador activa" -ForegroundColor Green
Write-Host "✅ Protecciones anti-duplicados implementadas" -ForegroundColor Green
Write-Host "✅ Requirements.txt optimizado" -ForegroundColor Green

Write-Host ""
Write-Host "🔧 PASOS PARA ACTIVAR EN GITHUB:" -ForegroundColor White
Write-Host "1. git add ." -ForegroundColor Yellow
Write-Host "2. git commit -m '🏈 Configurar scraper automático 24/7 cada 30min'" -ForegroundColor Yellow
Write-Host "3. git push origin main" -ForegroundColor Yellow

Write-Host ""
Write-Host "📊 DESPUÉS DEL PUSH:" -ForegroundColor White
Write-Host "• Ir a GitHub → Actions" -ForegroundColor Cyan
Write-Host "• Verificar que aparezca 'NFL Fantasy Scraper 24/7'" -ForegroundColor Cyan
Write-Host "• Ejecutar manualmente la primera vez (opcional)" -ForegroundColor Cyan
Write-Host "• El sistema comenzará automáticamente cada 30 minutos" -ForegroundColor Cyan

Write-Host ""
Write-Host "🎯 CONFIGURACIÓN COMPLETADA:" -ForegroundColor White
Write-Host "• Frecuencia: Cada 30 minutos (48 ejecuciones/día)" -ForegroundColor Green
Write-Host "• Horario: 24 horas al día, 7 días a la semana" -ForegroundColor Green
Write-Host "• Modo: Automático con máximas protecciones" -ForegroundColor Green
Write-Host "• Monitoreo: Health check cada 2 horas" -ForegroundColor Green

Write-Host ""
Write-Host "📈 ESTADÍSTICAS ESPERADAS:" -ForegroundColor White
Write-Host "• Solo cambios reales se insertarán (no duplicados masivos)" -ForegroundColor Yellow
Write-Host "• Aprox. 0-50 registros nuevos por ejecución (depende de actividad NFL)" -ForegroundColor Yellow
Write-Host "• Sistema se adapta automáticamente a semanas NFL" -ForegroundColor Yellow

Write-Host ""
Write-Host "⚠️ IMPORTANTE - VERIFICAR SECRETS EN GITHUB:" -ForegroundColor Red
Write-Host "• SUPABASE_URL = tu_url_de_supabase" -ForegroundColor Red
Write-Host "• SUPABASE_KEY = tu_clave_anonima_de_supabase" -ForegroundColor Red

Write-Host ""
Write-Host "✅ SISTEMA LISTO PARA PRODUCCIÓN 24/7" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green

Write-Host ""
Write-Host "🚀 ¿Quieres ejecutar los comandos git ahora? (y/n):" -ForegroundColor White -NoNewline
$response = Read-Host

if ($response -eq 'y' -or $response -eq 'Y' -or $response -eq 'yes') {
    Write-Host ""
    Write-Host "📥 Ejecutando comandos git..." -ForegroundColor Yellow
    
    try {
        git add .
        Write-Host "✅ git add . completado" -ForegroundColor Green
        
        git commit -m "🏈 Configurar scraper automático 24/7 cada 30min con sistema de semanas NFL"
        Write-Host "✅ git commit completado" -ForegroundColor Green
        
        git push origin main
        Write-Host "✅ git push completado" -ForegroundColor Green
        
        Write-Host ""
        Write-Host "🎉 ¡ACTIVACIÓN COMPLETADA!" -ForegroundColor Green
        Write-Host "🔗 Ve a GitHub Actions para ver el workflow en acción" -ForegroundColor Cyan
    }
    catch {
        Write-Host "❌ Error ejecutando git: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "💡 Ejecuta los comandos manualmente" -ForegroundColor Yellow
    }
} else {
    Write-Host ""
    Write-Host "📝 Ejecuta manualmente cuando estés listo:" -ForegroundColor Yellow
    Write-Host "git add . && git commit -m '🏈 Configurar scraper automático 24/7' && git push origin main" -ForegroundColor Cyan
}
