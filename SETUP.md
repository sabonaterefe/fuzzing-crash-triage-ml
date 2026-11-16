# Setup & Reproduction

## 1. Prerequisites (Ubuntu/WSL2)

    sudo apt update
    sudo apt install -y autoconf automake libtool m4 build-essential python3-venv gdb

Install AFL++: follow the official build instructions at
https://github.com/AFLplusplus/AFLplusplus

## 2. Build instrumented c-ares

    git clone https://github.com/c-ares/c-ares.git target/c-ares
    cd target/c-ares
    git checkout cares-1_12_0
    ./buildconf
    CC=afl-clang-fast CFLAGS="-fsanitize=address -g -O1 -fno-omit-frame-pointer" ./configure --disable-shared
    make -j$(nproc)

## 3. Build the harness and seed generator

    cd ../../src
    afl-clang-fast -fsanitize=address -g -O1 -fno-omit-frame-pointer \
      -I ../target/c-ares -o harness harness.c ../target/c-ares/.libs/libcares.a

    afl-clang-fast++ -std=c++11 -fsanitize=address \
      -I ../target/c-ares -I ../target/c-ares/test \
      seed_gen.cc ../target/c-ares/test/dns-proto.cc ../target/c-ares/.libs/libcares.a \

      -o seed_gen

    ./seed_gen
    cp seed_naptr_*.bin ../results/corpus/

## 4. Run the fuzzing campaign

    ASAN_OPTIONS=abort_on_error=1:symbolize=0 afl-fuzz \
      -i ../results/corpus \
      -o ../results/afl_output \
      -- ./harness @@

Run this inside tmux for long campaigns, and use AFL_AUTORESUME=1 to resume after any
interruption without losing progress.

## 5. Extract and cluster crashes

    python3 -m venv ~/fuzzing-env
    source ~/fuzzing-env/bin/activate
    pip install hdbscan scikit-learn numpy pandas

    cd ..
    python3 scripts/extract_traces.py
    python3 scripts/cluster_crashes.py

## 6. Verify the fix (regression test)

Apply docs/cve-2017-1000381-fix.patch to target/c-ares/ares_parse_naptr_reply.c, rebuild,
compile a separate harness_patched binary the same way as step 3, then re-run every crash
input in results/crashes/raw/ through it -- all should exit cleanly.
