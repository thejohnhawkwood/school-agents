"""
Answer Pattern QA and deterministic shuffle helpers for high-school test JSON specs.

Used by the test-builder workflow: detect suspicious correct-key patterns and
shuffle option/bank order with a seed derived from the test identifier.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from copy import deepcopy
from typing import Any, Iterable

# ---------------------------------------------------------------------------
# Seeding
# ---------------------------------------------------------------------------


def seed_from_test_id(test_id: str) -> int:
    """Return a stable 32-bit seed from ``test_id`` (UTF-8)."""
    digest = hashlib.sha256(test_id.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0xFFFFFFFF


def item_shuffle_seed(test_id: str, item_id: str) -> int:
    """Per-item seed so banks shuffle independently but reproducibly."""
    combined = f"{test_id}::{item_id}"
    digest = hashlib.sha256(combined.encode("utf-8")).digest()
    return int.from_bytes(digest[:4], "big") & 0xFFFFFFFF


# ---------------------------------------------------------------------------
# Shuffle (deterministic)
# ---------------------------------------------------------------------------


def shuffle_indices(n: int, seed: int) -> list[int]:
    """Return a permutation of ``range(n)`` using ``random.Random(seed)``."""
    rng = random.Random(seed)
    order = list(range(n))
    rng.shuffle(order)
    return order


def permute_list(items: list[Any], order: list[int]) -> list[Any]:
    return [items[i] for i in order]


def inverse_permutation(order: list[int]) -> list[int]:
    inv = [0] * len(order)
    for new_pos, old_pos in enumerate(order):
        inv[old_pos] = new_pos
    return inv


# ---------------------------------------------------------------------------
# Answer-key pattern QA
# ---------------------------------------------------------------------------

_KEY_RE = re.compile(r"^[A-Za-z0-9]$")


def normalize_key_token(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    if len(s) == 1 and _KEY_RE.match(s):
        return s.upper()
    return None


def detect_repeated_run(keys: list[str], max_run: int) -> list[dict[str, Any]]:
    """Flag runs of the same key longer than ``max_run``."""
    violations: list[dict[str, Any]] = []
    if max_run < 1:
        return violations
    i = 0
    while i < len(keys):
        j = i + 1
        while j < len(keys) and keys[j] == keys[i]:
            j += 1
        run_len = j - i
        if run_len > max_run:
            violations.append(
                {
                    "type": "repeated_run",
                    "key": keys[i],
                    "start_index": i,
                    "end_index": j - 1,
                    "length": run_len,
                    "max_allowed": max_run,
                }
            )
        i = j
    return violations


def detect_exact_cycle(keys: list[str], max_period: int = 6) -> list[dict[str, Any]]:
    """
    Flag sequences that are a perfect repetition of a short pattern, e.g.
    ABABAB (period 2) or ABCABC (period 3).
    """
    violations: list[dict[str, Any]] = []
    n = len(keys)
    if n < 4:
        return violations
    upper_p = min(max_period, n // 2)
    for p in range(2, upper_p + 1):
        if n % p != 0:
            continue
        pattern = keys[:p]
        ok = all(keys[i] == pattern[i % p] for i in range(n))
        if ok and n >= p * 3:
            violations.append(
                {
                    "type": "exact_cycle",
                    "period": p,
                    "pattern": pattern,
                    "length": n,
                }
            )
    return violations


def answer_pattern_qa(
    keys: list[str],
    *,
    max_run: int = 3,
    max_cycle_period: int = 6,
) -> dict[str, Any]:
    """
    Run Answer Pattern QA on a list of keyed tokens (e.g. multiple-choice letters).

    Unknown / empty tokens are skipped for pattern checks (caller should filter).
    """
    normalized = [k for k in (normalize_key_token(x) for x in keys) if k is not None]
    runs = detect_repeated_run(normalized, max_run)
    cycles = detect_exact_cycle(normalized, max_cycle_period)
    violations = runs + cycles
    return {
        "keys_evaluated": normalized,
        "violation_count": len(violations),
        "violations": violations,
        "passes": len(violations) == 0,
    }


# ---------------------------------------------------------------------------
# Item spec shuffle + QA (minimal schema)
# ---------------------------------------------------------------------------


def _shuffle_multiple_choice_item(item: dict[str, Any], test_id: str) -> dict[str, Any]:
    out = deepcopy(item)
    choices = out.get("choices")
    if not isinstance(choices, list) or len(choices) < 2:
        return out
    ci = out.get("correct_index")
    ak = normalize_key_token(out.get("answer_key")) if out.get("answer_key") is not None else None
    if not isinstance(ci, int) or ci < 0 or ci >= len(choices):
        if ak is not None and len(ak) == 1:
            ci = ord(ak) - ord("A")
        else:
            return out
    if not isinstance(ci, int) or ci < 0 or ci >= len(choices):
        return out
    item_id = str(out.get("id", ""))
    order = shuffle_indices(len(choices), item_shuffle_seed(test_id, item_id or "unknown"))
    inv = inverse_permutation(order)
    out["choices"] = permute_list(choices, order)
    out["correct_index"] = int(inv[ci])
    out["answer_key"] = chr(ord("A") + int(out["correct_index"]))
    out.setdefault("randomization", {})
    if isinstance(out["randomization"], dict):
        out["randomization"]["choice_shuffle_order"] = order
        out["randomization"]["seed_basis"] = "test_id+item_id"
    return out


def _shuffle_word_bank_item(item: dict[str, Any], test_id: str) -> dict[str, Any]:
    out = deepcopy(item)
    bank = out.get("word_bank")
    if not isinstance(bank, list) or len(bank) < 2:
        return out
    item_id = str(out.get("id", ""))
    order = shuffle_indices(len(bank), item_shuffle_seed(test_id, f"{item_id}:word_bank"))
    out["word_bank"] = permute_list(bank, order)
    out.setdefault("randomization", {})
    if isinstance(out["randomization"], dict):
        out["randomization"]["word_bank_shuffle_order"] = order
    return out


def _shuffle_matching_item(item: dict[str, Any], test_id: str) -> dict[str, Any]:
    """
    Shuffle display order of ``right_options`` only.

    Each right option should keep a stable ``id`` (if dict). ``correct_map``
    then stays unchanged because it references ids, not display positions.
    """
    out = deepcopy(item)
    rights = out.get("right_options")
    if not isinstance(rights, list) or len(rights) < 2:
        return out
    item_id = str(out.get("id", ""))
    order = shuffle_indices(len(rights), item_shuffle_seed(test_id, f"{item_id}:matching_right"))

    permuted = permute_list(list(rights), order)

    out["right_options"] = permuted
    out.setdefault("randomization", {})
    if isinstance(out["randomization"], dict):
        out["randomization"]["right_options_shuffle_order"] = order
    return out


def apply_deterministic_shuffles(spec: dict[str, Any]) -> dict[str, Any]:
    """
    Return a deep copy of ``spec`` with shuffles applied per item type.

    Expected keys on root: ``test_id``, ``items`` (list of item dicts).
    Item ``type``: ``multiple_choice`` | ``matching`` | ``diagram_labeling`` (word bank).
    """
    out = deepcopy(spec)
    test_id = str(out.get("test_id", "default-test"))
    items = out.get("items")
    if not isinstance(items, list):
        return out
    new_items: list[Any] = []
    for it in items:
        if not isinstance(it, dict):
            new_items.append(it)
            continue
        t = str(it.get("type", "")).lower()
        if t == "multiple_choice":
            new_items.append(_shuffle_multiple_choice_item(it, test_id))
        elif t == "matching":
            new_items.append(_shuffle_matching_item(it, test_id))
        elif t in ("diagram_labeling", "labeling"):
            new_items.append(_shuffle_word_bank_item(it, test_id))
        else:
            new_items.append(deepcopy(it))
    out["items"] = new_items
    return out


def extract_answer_key_sequence(spec: dict[str, Any]) -> list[str]:
    """Collect ``answer_key`` tokens from items in order (MC letters, etc.)."""
    keys: list[str] = []
    items = spec.get("items")
    if not isinstance(items, list):
        return keys
    for it in items:
        if not isinstance(it, dict):
            continue
        ak = it.get("answer_key")
        if ak is not None:
            keys.append(str(ak))
        elif str(it.get("type", "")).lower() == "multiple_choice":
            choices = it.get("choices")
            ci = it.get("correct_index")
            if isinstance(choices, list) and isinstance(ci, int) and 0 <= ci < len(choices):
                keys.append(chr(ord("A") + ci))
    return keys


def spec_answer_pattern_qa(
    spec: dict[str, Any],
    *,
    max_run: int = 3,
    max_cycle_period: int = 6,
) -> dict[str, Any]:
    keys = extract_answer_key_sequence(spec)
    report = answer_pattern_qa(keys, max_run=max_run, max_cycle_period=max_cycle_period)
    report["raw_keys"] = keys
    return report


def process_spec_file(
    path: str,
    *,
    shuffle: bool,
    max_run: int = 3,
    max_cycle_period: int = 6,
) -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        spec = json.load(f)
    if shuffle:
        spec = apply_deterministic_shuffles(spec)
    qa = spec_answer_pattern_qa(spec, max_run=max_run, max_cycle_period=max_cycle_period)
    return {"spec": spec, "qa": qa}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Test builder answer-pattern QA and shuffle.")
    p.add_argument("--keys", nargs="*", help="Raw key tokens in order (e.g. A B B A C)")
    p.add_argument("--spec", help="Path to item specification JSON")
    p.add_argument("--shuffle-spec", action="store_true", help="Apply deterministic shuffles before QA")
    p.add_argument("--out", help="Write processed spec JSON to this path")
    p.add_argument("--max-run", type=int, default=3, help="Max allowed same-key run length")
    p.add_argument("--max-cycle-period", type=int, default=6)
    args = p.parse_args(argv)

    if args.keys is not None and len(args.keys) > 0:
        report = answer_pattern_qa(args.keys, max_run=args.max_run, max_cycle_period=args.max_cycle_period)
        print(json.dumps(report, indent=2))
        return 0 if report["passes"] else 1

    if args.spec:
        result = process_spec_file(args.spec, shuffle=args.shuffle_spec, max_run=args.max_run, max_cycle_period=args.max_cycle_period)
        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(result["spec"], f, indent=2)
                f.write("\n")
        print(json.dumps(result["qa"], indent=2))
        return 0 if result["qa"]["passes"] else 1

    p.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
