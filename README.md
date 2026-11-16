# ML-Assisted Crash Triage for Coverage-Guided Fuzzing

Fuzzing the c-ares DNS library with AFL++ and AddressSanitizer, rediscovering a real,
documented vulnerability (**CVE-2017-1000381**) from scratch, and triaging the resulting
crashes with density-based clustering (**HDBSCAN**) instead of manually reading every stack
trace by hand.

**[Read the full write-up](https://sabonaterefe.github.io/fuzzing-crash-triage-ml/)**

## Results at a glance

- **16 unique crashes** found over a 9+ day fuzzing campaign (3,056 cycles)
- **3 triage methods compared**: naive dedup (fails, 16/16 "unique"), frame-signature matching (collapses to 1 group), HDBSCAN (correctly finds 2 real sub-clusters, 0 noise)
- **Root cause confirmed** against the real upstream CVE-2017-1000381 patch
- **16/16 crashes resolved** by the real fix, verified via regression testing

## Repository structure

    docs/        Write-up (GitHub Pages) + the actual CVE fix patch
    scripts/     extract_traces.py (crash -> stack trace), cluster_crashes.py (triage)
    src/         Fuzzing harness, DNS seed generator
    results/     Crash records, cluster output, regression test results
    target/      Vendored c-ares (not committed -- see SETUP.md)
    SETUP.md     Full reproduction steps

## Reproducing this

See [SETUP.md](SETUP.md) for the full build and fuzzing setup.

## Stack


AFL++ - AddressSanitizer - c-ares - Python (HDBSCAN, scikit-learn) - WSL2
