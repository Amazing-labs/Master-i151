# Linux runtime for Arena benchmarks in isolated mode (the competition mode).
# `arena match --isolated` relies on select() over pipes, which fails on Windows.
#
# The project is bind-mounted at /work at run time (see scripts/bench.ps1),
# so editing a bot does not require rebuilding the image.
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1

RUN pip install --no-cache-dir --root-user-action=ignore \
    i151-arena-sdk==0.2.10 \
    i151-engine==0.2.4

WORKDIR /work
