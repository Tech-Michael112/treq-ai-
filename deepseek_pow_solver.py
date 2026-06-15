#!/usr/bin/env python3
"""
deepseek_pow_solver.py
======================
Single-file DeepSeek Proof-of-Work solver.
Reconstructed from pow_solver.py (images) + DeepSeek_pow_challenge.py (zip).
Original author credit: BY AHMED_ALHRRANI

What it does
------------
DeepSeek's API requires solving a PoW challenge before requests are accepted.
The challenge: find the smallest integer nonce n in [0, difficulty) such that

    deepseek_hash(base.encode() + str(n).encode()) == bytes.fromhex(challenge)

where deepseek_hash is a custom Keccak variant (rate=136, outlen=32, 23 rounds).

Usage (CLI)
-----------
    python deepseek_pow_solver.py <base> <challenge_hex> <difficulty>

    python deepseek_pow_solver.py \\
        "0d3c841b8d8d02acb7d3_1766266237599_" \\
        "c35483aecce7e4d151fd16541f23a4058690a0b8ef94cfcab38f16409cae0955" \\
        144000

Usage (as a library)
--------------------
    from deepseek_pow_solver import solve, deepseek_hash
    nonce = solve(base, challenge_hex, difficulty)

Backends
--------
  1. Native  – uses libsolver.so (place in ./lib/<arch>/) if present → fast
  2. Python  – pure-Python fallback, no dependencies → slower but portable
"""

import sys
import os
import platform
import ctypes

# ═══════════════════════════════════════════════════════════════
#  Keccak-f[1600] constants
#  Standard 24 round constants; DeepSeek's hash uses _RC[1:24]
#  (23 rounds, intentionally skipping RC[0]).
# ═══════════════════════════════════════════════════════════════

_M = (1 << 64) - 1  # 64-bit lane mask

_RC = [
    0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
    0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
    0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
    0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
    0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
    0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008,
]

_RC23 = _RC[1:24]   # DeepSeek skips RC[0] → 23 rounds

# ═══════════════════════════════════════════════════════════════
#  Keccak-f[1600] permutation (θ → ρπ → χ → ι)
# ═══════════════════════════════════════════════════════════════

def _keccakf(L):
    (a00, a01, a02, a03, a04, a05, a06, a07, a08, a09, a10, a11, a12,
     a13, a14, a15, a16, a17, a18, a19, a20, a21, a22, a23, a24) = L

    for rc in _RC23:
        # ── θ (theta) ──────────────────────────────────────────
        c0 = a00 ^ a05 ^ a10 ^ a15 ^ a20
        c1 = a01 ^ a06 ^ a11 ^ a16 ^ a21
        c2 = a02 ^ a07 ^ a12 ^ a17 ^ a22
        c3 = a03 ^ a08 ^ a13 ^ a18 ^ a23
        c4 = a04 ^ a09 ^ a14 ^ a19 ^ a24
        d0 = c4 ^ (((c1 << 1) | (c1 >> 63)) & _M)
        d1 = c0 ^ (((c2 << 1) | (c2 >> 63)) & _M)
        d2 = c1 ^ (((c3 << 1) | (c3 >> 63)) & _M)
        d3 = c2 ^ (((c4 << 1) | (c4 >> 63)) & _M)
        d4 = c3 ^ (((c0 << 1) | (c0 >> 63)) & _M)
        a00 ^= d0; a05 ^= d0; a10 ^= d0; a15 ^= d0; a20 ^= d0
        a01 ^= d1; a06 ^= d1; a11 ^= d1; a16 ^= d1; a21 ^= d1
        a02 ^= d2; a07 ^= d2; a12 ^= d2; a17 ^= d2; a22 ^= d2
        a03 ^= d3; a08 ^= d3; a13 ^= d3; a18 ^= d3; a23 ^= d3
        a04 ^= d4; a09 ^= d4; a14 ^= d4; a19 ^= d4; a24 ^= d4

        # ── ρ + π (rho + pi, combined into a single b-array) ───
        b00 = a00
        b01 = ((a06 << 44) | (a06 >> 20)) & _M
        b02 = ((a12 << 43) | (a12 >> 21)) & _M
        b03 = ((a18 << 21) | (a18 >> 43)) & _M
        b04 = ((a24 << 14) | (a24 >> 50)) & _M
        b05 = ((a03 << 28) | (a03 >> 36)) & _M
        b06 = ((a09 << 20) | (a09 >> 44)) & _M
        b07 = ((a10 <<  3) | (a10 >> 61)) & _M
        b08 = ((a16 << 45) | (a16 >> 19)) & _M
        b09 = ((a22 << 61) | (a22 >>  3)) & _M
        b10 = ((a01 <<  1) | (a01 >> 63)) & _M
        b11 = ((a07 <<  6) | (a07 >> 58)) & _M
        b12 = ((a13 << 25) | (a13 >> 39)) & _M
        b13 = ((a19 <<  8) | (a19 >> 56)) & _M
        b14 = ((a20 << 18) | (a20 >> 46)) & _M
        b15 = ((a04 << 27) | (a04 >> 37)) & _M
        b16 = ((a05 << 36) | (a05 >> 28)) & _M
        b17 = ((a11 << 10) | (a11 >> 54)) & _M
        b18 = ((a17 << 15) | (a17 >> 49)) & _M
        b19 = ((a23 << 56) | (a23 >>  8)) & _M
        b20 = ((a02 << 62) | (a02 >>  2)) & _M
        b21 = ((a08 << 55) | (a08 >>  9)) & _M
        b22 = ((a14 << 39) | (a14 >> 25)) & _M
        b23 = ((a15 << 41) | (a15 >> 23)) & _M
        b24 = ((a21 <<  2) | (a21 >> 62)) & _M

        # ── χ (chi) ────────────────────────────────────────────
        a00 = b00 ^ ((~b01) & b02); a01 = b01 ^ ((~b02) & b03); a02 = b02 ^ ((~b03) & b04)
        a03 = b03 ^ ((~b04) & b00); a04 = b04 ^ ((~b00) & b01)
        a05 = b05 ^ ((~b06) & b07); a06 = b06 ^ ((~b07) & b08); a07 = b07 ^ ((~b08) & b09)
        a08 = b08 ^ ((~b09) & b05); a09 = b09 ^ ((~b05) & b06)
        a10 = b10 ^ ((~b11) & b12); a11 = b11 ^ ((~b12) & b13); a12 = b12 ^ ((~b13) & b14)
        a13 = b13 ^ ((~b14) & b10); a14 = b14 ^ ((~b10) & b11)
        a15 = b15 ^ ((~b16) & b17); a16 = b16 ^ ((~b17) & b18); a17 = b17 ^ ((~b18) & b19)
        a18 = b18 ^ ((~b19) & b15); a19 = b19 ^ ((~b15) & b16)
        a20 = b20 ^ ((~b21) & b22); a21 = b21 ^ ((~b22) & b23); a22 = b22 ^ ((~b23) & b24)
        a23 = b23 ^ ((~b24) & b20); a24 = b24 ^ ((~b20) & b21)

        # ── ι (iota) ───────────────────────────────────────────
        a00 ^= rc

    return [
        a00 & _M, a01 & _M, a02 & _M, a03 & _M, a04 & _M,
        a05 & _M, a06 & _M, a07 & _M, a08 & _M, a09 & _M,
        a10 & _M, a11 & _M, a12 & _M, a13 & _M, a14 & _M,
        a15 & _M, a16 & _M, a17 & _M, a18 & _M, a19 & _M,
        a20 & _M, a21 & _M, a22 & _M, a23 & _M, a24 & _M,
    ]

# ═══════════════════════════════════════════════════════════════
#  DeepSeek hash  (Keccak sponge, rate=136 bytes, output=32 bytes)
# ═══════════════════════════════════════════════════════════════

def deepseek_hash(data: bytes, rate: int = 136, outlen: int = 32) -> bytes:
    """Custom Keccak-based hash used by DeepSeek's PoW system."""
    st  = [0] * 25
    off = 0
    n   = len(data)

    # absorb full blocks
    while n - off >= rate:
        for i in range(rate // 8):
            st[i] ^= int.from_bytes(data[off + 8 * i : off + 8 * i + 8], "little")
        st   = _keccakf(st)
        off += rate

    # padding (Keccak-style with 0x06 suffix, not SHA-3's 0x01)
    rem = bytearray(data[off:])
    rem.append(0x06)
    rem.extend(b'\x00' * (rate - len(rem)))
    rem[-1] |= 0x80
    for i in range(rate // 8):
        st[i] ^= int.from_bytes(rem[8 * i : 8 * i + 8], "little")
    st = _keccakf(st)

    # squeeze
    out = bytearray()
    while len(out) < outlen:
        for i in range(rate // 8):
            out += st[i].to_bytes(8, "little")
        if len(out) < outlen:
            st = _keccakf(st)

    return bytes(out[:outlen])

# ═══════════════════════════════════════════════════════════════
#  Pure-Python brute-force solver
# ═══════════════════════════════════════════════════════════════

def _solve_py(base: str, challenge: str, difficulty: int) -> int:
    """Iterate nonces 0..difficulty-1; return first match or -1."""
    target = bytes.fromhex(challenge)
    base_b = base.encode()
    for nonce in range(int(difficulty)):
        if deepseek_hash(base_b + str(nonce).encode()) == target:
            return nonce
    return -1

# ═══════════════════════════════════════════════════════════════
#  Optional native (C) solver via libsolver.so
# ═══════════════════════════════════════════════════════════════

_ARCH_DIRS = {
    "aarch64": "arm64-v8a",  "arm64":  "arm64-v8a",
    "armv7l":  "armeabi-v7a","armv8l": "armeabi-v7a", "armv7": "armeabi-v7a",
    "x86_64":  "x86_64",     "amd64":  "x86_64",
    "i686":    "x86",        "i386":   "x86",         "x86":   "x86",
}

_native = None   # None = not yet tried, False = unavailable, callable = loaded

def _load_native():
    """Try to load libsolver.so for the current CPU architecture.
    Expects the file at:  ./lib/<arch>/libsolver.so
    Returns a callable or False.
    """
    global _native
    if _native is not None:
        return _native
    try:
        arch = _ARCH_DIRS.get(platform.machine().lower())
        here = os.path.dirname(os.path.abspath(__file__))
        so   = os.path.join(here, "lib", arch or "", "libsolver.so")
        if not arch or not os.path.exists(so):
            _native = False
            return _native
        lib              = ctypes.CDLL(so)
        fn               = lib.deepseek_hash_solve
        fn.restype       = ctypes.c_int64
        fn.argtypes      = [ctypes.c_char_p, ctypes.c_size_t,
                             ctypes.c_char_p, ctypes.c_size_t,
                             ctypes.c_int64]

        def _call(base: str, challenge: str, difficulty: int) -> int:
            cb, bb = challenge.encode(), base.encode()
            return int(fn(cb, len(cb), bb, len(bb), int(difficulty)))

        _native = _call
    except Exception:
        _native = False
    return _native

# ═══════════════════════════════════════════════════════════════
#  Public API
# ═══════════════════════════════════════════════════════════════

def solve(base: str, challenge: str, difficulty: int) -> int:
    """Solve a DeepSeek PoW challenge.

    Parameters
    ----------
    base       : salt string (e.g. "0d3c841b8d8d02acb7d3_1766266237599_")
    challenge  : expected hash as a hex string (64 hex chars = 32 bytes)
    difficulty : search range [0, difficulty)

    Returns
    -------
    nonce (int) on success, or -1 if no solution found.
    """
    native = _load_native()
    if native:
        return native(base, challenge, difficulty)
    return _solve_py(base, challenge, difficulty)

# ═══════════════════════════════════════════════════════════════
#  CLI entry-point  (replaces both solve.jar and the Java call)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python deepseek_pow_solver.py <base> <challenge_hex> <difficulty>")
        print()
        print("Example:")
        print('  python deepseek_pow_solver.py \\')
        print('      "0d3c841b8d8d02acb7d3_1766266237599_" \\')
        print('      "c35483aecce7e4d151fd16541f23a4058690a0b8ef94cfcab38f16409cae0955" \\')
        print('      144000')
        sys.exit(1)

    base_arg       = sys.argv[1]
    challenge_arg  = sys.argv[2]
    difficulty_arg = int(sys.argv[3])

    using_native = bool(_load_native())
    print(f"[*] Backend    : {'native libsolver.so' if using_native else 'pure Python'}")
    print(f"[*] Base       : {base_arg}")
    print(f"[*] Challenge  : {challenge_arg}")
    print(f"[*] Difficulty : {difficulty_arg:,}")
    print("[*] Solving ...", flush=True)

    result = solve(base_arg, challenge_arg, difficulty_arg)

    if result == -1:
        print("[-] No solution found within the difficulty range.")
        sys.exit(1)
    else:
        print(f"[+] Nonce      : {result}")
