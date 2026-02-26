# Run this script after installing Git: https://git-scm.com/download/win
# In PowerShell: .\setup-git.ps1

Set-Location $PSScriptRoot

git init
git add .
git commit -m "chore: initial scaffold"
git branch -M main
git remote add origin https://github.com/haseebpytdev/jobpulse-lahore.git
git push -u origin main
