# Get the current username
$currentUser = $env:USERNAME

# Query all user sessions
$queryResult = query user

# Find the line that contains the current user
$userLine = ($queryResult | ForEach-Object { $_ }) -match $currentUser

# Extract the session ID (3rd token from the matched line)
$sessionId = ($userLine -split '\s+')[2]

# Reconnect the session to the console with elevation
Start-Process "$env:windir\System32\tscon.exe" -ArgumentList "$sessionId /dest:console" -Verb RunAs