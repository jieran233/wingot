$folder = Split-Path $MyInvocation.MyCommand.Path
Set-Location -Path $folder
python .\wingot.py