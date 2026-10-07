# Minimal static file server (no Node/Python needed). For local development only.
# Usage: powershell -ExecutionPolicy Bypass -File serve.ps1 [-Port 5173] [-ApiOrigin http://localhost:3000]
# -ApiOrigin: the origin of the real backend (API_MODE "http"). It is added to the CSP connect-src.
param([int]$Port = 5173, [string]$ApiOrigin = "")

# Accept only a plain origin (scheme + host + optional port), so the CSP header cannot be changed
if ($ApiOrigin -and $ApiOrigin -notmatch '^https?://[A-Za-z0-9.-]+(:\d{1,5})?$') {
  Write-Error "ApiOrigin must look like http://localhost:3000"
  exit 1
}

$root = [IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\') + '\'
$listener = New-Object System.Net.HttpListener
$listener.Prefixes.Add("http://localhost:$Port/")
$listener.Start()
Write-Host "Jinder running at http://localhost:$Port/  (Ctrl+C to stop)"

# Only these file types are served. All other files (for example, this script) return 404.
$types = @{
  ".html" = "text/html; charset=utf-8"; ".css" = "text/css; charset=utf-8"
  ".js" = "application/javascript; charset=utf-8"; ".svg" = "image/svg+xml"
  ".png" = "image/png"; ".jpg" = "image/jpeg"; ".ico" = "image/x-icon"; ".json" = "application/json"
}

# Security headers. The CSP allows only own files plus Google Fonts.
# No inline scripts or inline style attributes are allowed. Keep JS and CSS in files.
$csp = "default-src 'self'; script-src 'self'; style-src 'self' https://fonts.googleapis.com; " +
       "font-src https://fonts.gstatic.com; img-src 'self' data:; connect-src 'self' $ApiOrigin; " +
       "object-src 'none'; base-uri 'self'; form-action 'self'; frame-ancestors 'none'"
$headers = [ordered]@{
  "Content-Security-Policy" = $csp
  "X-Content-Type-Options"  = "nosniff"
  "X-Frame-Options"         = "DENY"
  "Referrer-Policy"         = "strict-origin-when-cross-origin"
  "Permissions-Policy"      = "camera=(), microphone=(), geolocation=()"
  "Cache-Control"           = "no-cache"
}

try {
  while ($listener.IsListening) {
    $ctx = $listener.GetContext()
    $res = $ctx.Response
    foreach ($h in $headers.GetEnumerator()) { $res.Headers[$h.Key] = $h.Value }

    if ($ctx.Request.HttpMethod -notin @("GET", "HEAD")) {
      $res.StatusCode = 405
      $res.Close()
      continue
    }

    $path = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath).TrimStart("/")
    if ($path -eq "") { $path = "index.html" }
    $file = [IO.Path]::GetFullPath((Join-Path $root $path))
    $ext = [IO.Path]::GetExtension($file).ToLower()

    # Block path traversal: the file must be inside the app folder.
    $inside = $file.StartsWith($root, [StringComparison]::OrdinalIgnoreCase)
    if ($inside -and $types.ContainsKey($ext) -and (Test-Path $file -PathType Leaf)) {
      $bytes = [IO.File]::ReadAllBytes($file)
      $res.ContentType = $types[$ext]
      # The logo symbol in icons.svg uses inline styles. SVG files get a CSP with no scripts and inline styles only.
      if ($ext -eq ".svg") { $res.Headers["Content-Security-Policy"] = "default-src 'none'; style-src 'unsafe-inline'" }
      $res.StatusCode = 200
    } else {
      $bytes = [Text.Encoding]::UTF8.GetBytes("404 Not Found")
      $res.ContentType = "text/plain; charset=utf-8"
      $res.StatusCode = 404
    }
    if ($ctx.Request.HttpMethod -eq "GET") { $res.OutputStream.Write($bytes, 0, $bytes.Length) }
    $res.Close()
  }
} finally {
  $listener.Stop()
}
