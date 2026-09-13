Add-Type -AssemblyName System.Drawing

$size = 256
$bmp = New-Object System.Drawing.Bitmap($size, $size)
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$g.Clear([System.Drawing.Color]::Transparent)
$g.TranslateTransform(128, 128)

$goldLight = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 255, 197, 61))
$goldDark = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 245, 166, 35))
$seedDark = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 138, 90, 43))
$seedLight = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::FromArgb(255, 160, 108, 53))

for ($i = 0; $i -lt 16; $i++) {
    $g.RotateTransform(22.5)
    $brush = if ($i % 2 -eq 0) { $goldLight } else { $goldDark }
    $g.FillEllipse($brush, -20, -112, 40, 74)
}
$g.FillEllipse($seedDark, -50, -50, 100, 100)
$g.FillEllipse($seedLight, -36, -36, 72, 72)
$g.Dispose()

$icoPath = Join-Path $PSScriptRoot 'agentforge.ico'
$icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())
$fs = [System.IO.File]::Create($icoPath)
$icon.Save($fs)
$fs.Close()
$bmp.Dispose()
Write-Host "icon saved: $icoPath"
