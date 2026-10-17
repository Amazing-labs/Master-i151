# Runs scripts/benchmark.py inside the Linux Arena image (isolated mode).
# Examples:
#   .\scripts\bench.ps1 run bot.py --panel 777 --games 1000
#   .\scripts\bench.ps1 compare bot bot_v2_1 --panel 777
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

docker build --quiet --tag master-i151-arena $root | Out-Null
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

docker run --rm --volume "${root}:/work" master-i151-arena python scripts/benchmark.py @args
exit $LASTEXITCODE
