$ErrorActionPreference = "Continue"
Set-Location "c:\appAI\quant"

"===== GIT STATUS =====" | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
git status 2>&1 | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append

"`n===== BRANCH =====" | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
git branch --show-current 2>&1 | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
git branch -a 2>&1 | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append

"`n===== LOG =====" | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
git log --oneline -3 2>&1 | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append

"`n===== REMOTE =====" | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
git remote -v 2>&1 | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append

"DONE" | Out-File -FilePath "c:\appAI\quant\git_debug.log" -Encoding UTF8 -Append
