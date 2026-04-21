#!/usr/bin/env python3
"""
view_grace_memory.py
Browse all of GRACE's memory stores from the terminal.

Usage:
    python3 view_grace_memory.py
    python3 view_grace_memory.py --db episodic
    python3 view_grace_memory.py --db semantic
    python3 view_grace_memory.py --db conversation
    python3 view_grace_memory.py --db procedural
    python3 view_grace_memory.py --db social
    python3 view_grace_memory.py --db personality
    python3 view_grace_memory.py --db values
    python3 view_grace_memory.py --db narrative
    python3 view_grace_memory.py --search "keyword"
"""
import json, os, sys, argparse, time

# ── ANSI ──────────────────────────────────────────────────────────────────────
CYAN    = "\033[96m"
GREEN   = "\033[92m"
YELLOW  = "\033[93m"
MAGENTA = "\033[95m"
RED     = "\033[91m"
BLUE    = "\033[94m"
WHITE   = "\033[97m"
RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"

MEMORY_DIR = "/home/grace/memory"

STORES = {
    "episodic":     "episodic.json",
    "semantic":     "semantic.json",
    "procedural":   "procedural.json",
    "social":       "social.json",
    "conversation": "conversation.json",
    "personality":  "personality.json",
    "values":       "values.json",
    "narrative":    "narrative.json",
}


def load(filename):
    path = os.path.join(MEMORY_DIR, filename)
    if not os.path.exists(path):
        return []
    try:
        with open(path) as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"{RED}Error loading {path}: {e}{RESET}")
        return []


def fmt_time(ts):
    if not ts:
        return "?"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return str(ts)


def bar(val, width=10, color=GREEN):
    try:
        v = float(val)
        filled = int(max(0.0, min(1.0, v)) * width)
        return f"{color}{'█'*filled}{'░'*(width-filled)}{RESET}"
    except Exception:
        return "?" * width


def print_entry(entry, idx, verbose=False):
    if not isinstance(entry, dict):
        print(f"  {DIM}[{idx}] {entry}{RESET}")
        return

    # Skip KV meta entries
    if "_kv" in entry:
        kv = entry["_kv"]
        print(f"\n{CYAN}{BOLD}  [KV store]{RESET}")
        for k, v in kv.items():
            if isinstance(v, dict):
                print(f"  {BOLD}{k}:{RESET}")
                for kk, vv in v.items():
                    if isinstance(vv, (int, float)):
                        print(f"    {DIM}{kk:<28}{RESET} {bar(vv)} {vv:.4f}")
                    else:
                        print(f"    {DIM}{kk:<28}{RESET} {str(vv)[:60]}")
            else:
                print(f"  {BOLD}{k}:{RESET} {str(v)[:80]}")
        return

    ts      = entry.get("timestamp", "")
    mtype   = entry.get("memory_type", entry.get("role", ""))
    content = entry.get("content", entry.get("text", ""))
    tags    = entry.get("tags", [])
    etag    = entry.get("emotional_tag", None)
    conf    = entry.get("confidence", None)

    # Colour by type
    type_colors = {
        "episodic":   MAGENTA,
        "semantic":   CYAN,
        "procedural": GREEN,
        "social":     YELLOW,
        "user":       BLUE,
        "assistant":  GREEN,
    }
    tc = type_colors.get(mtype, WHITE)

    print(f"\n{DIM}  ─── [{idx}] {fmt_time(ts)}{RESET}")
    if mtype:
        print(f"  {tc}{BOLD}{mtype.upper()}{RESET}", end="")
    if tags:
        print(f"  {DIM}{' '.join(f'#{t}' for t in tags)}{RESET}", end="")
    if etag is not None:
        print(f"  {DIM}emotion:{bar(etag, 6, MAGENTA)}{RESET}", end="")
    if conf is not None:
        print(f"  {DIM}conf:{bar(conf, 6, GREEN)}{RESET}", end="")
    print()

    # Content
    if content:
        lines = content.split("\n")
        for line in lines:
            if len(line) > 100:
                # Wrap long lines
                while line:
                    print(f"    {line[:100]}")
                    line = line[100:]
            else:
                print(f"    {line}")

    # Show extra fields in verbose mode
    if verbose:
        for k, v in entry.items():
            if k not in ("timestamp","memory_type","content","tags",
                         "emotional_tag","confidence","role","text"):
                print(f"  {DIM}  {k}: {str(v)[:80]}{RESET}")

    # Special handling for procedural skills
    if "skill" in entry:
        prof = entry.get("proficiency", 0)
        skill_tags = entry.get("tags", [])
        print(f"    {GREEN}{BOLD}{entry['skill']}{RESET}  "
              f"{bar(prof)} {prof:.2f}  "
              f"{DIM}{' '.join(skill_tags)}{RESET}")


def show_store(name, filename, search=None, tail=None, verbose=False):
    entries = load(filename)

    # Filter
    if search:
        q = search.lower()
        entries = [e for e in entries
                   if q in json.dumps(e).lower()]

    total = len(entries)

    print(f"\n{CYAN}{BOLD}{'═'*60}{RESET}")
    print(f"{CYAN}{BOLD}  {name.upper()} MEMORY{RESET}"
          f"  {DIM}{total} entries  {os.path.join(MEMORY_DIR, filename)}{RESET}")
    print(f"{CYAN}{BOLD}{'═'*60}{RESET}")

    if not entries:
        print(f"  {DIM}(empty){RESET}")
        return

    # Show tail or all
    if tail:
        show = entries[-tail:]
        if total > tail:
            print(f"  {DIM}... showing last {tail} of {total} entries ...{RESET}")
    else:
        show = entries

    for i, entry in enumerate(show):
        print_entry(entry, total - len(show) + i + 1, verbose=verbose)

    print()


def show_summary():
    print(f"\n{CYAN}{BOLD}{'═'*60}{RESET}")
    print(f"{CYAN}{BOLD}  GRACE MEMORY SUMMARY{RESET}")
    print(f"{CYAN}{BOLD}{'═'*60}{RESET}\n")

    for name, filename in STORES.items():
        path = os.path.join(MEMORY_DIR, filename)
        if os.path.exists(path):
            try:
                with open(path) as f:
                    data = json.load(f)
                count = len(data) if isinstance(data, list) else 0
                size  = os.path.getsize(path)
                size_s = f"{size/1024:.1f}KB" if size > 1024 else f"{size}B"

                # Most recent entry
                recent = ""
                if count > 0:
                    last = data[-1]
                    if isinstance(last, dict):
                        recent = last.get("content", last.get("role",""))[:50]

                color = GREEN if count > 0 else DIM
                print(f"  {color}{'●' if count>0 else '○'}{RESET} "
                      f"{BOLD}{name:<15}{RESET} "
                      f"{DIM}{count:>4} entries  {size_s:<8}{RESET} "
                      f"{DIM}{recent}{RESET}")
            except Exception:
                print(f"  {RED}○{RESET} {name:<15} {DIM}(error reading){RESET}")
        else:
            print(f"  {RED}○{RESET} {BOLD}{name:<15}{RESET} {DIM}(not found){RESET}")

    print()
    print(f"  {DIM}Usage:{RESET}")
    print(f"  {DIM}  python3 view_grace_memory.py --db episodic{RESET}")
    print(f"  {DIM}  python3 view_grace_memory.py --db conversation --tail 10{RESET}")
    print(f"  {DIM}  python3 view_grace_memory.py --search 'keyword'{RESET}")
    print(f"  {DIM}  python3 view_grace_memory.py --all{RESET}")
    print()


def main():
    global MEMORY_DIR
    parser = argparse.ArgumentParser(description="Browse GRACE's memory")
    parser.add_argument("--db",     help="Memory store to view")
    parser.add_argument("--search", help="Search keyword across all stores")
    parser.add_argument("--tail",   type=int, default=20,
                        help="Show last N entries (default 20)")
    parser.add_argument("--all",    action="store_true",
                        help="Show all entries (no tail limit)")
    parser.add_argument("--verbose",action="store_true",
                        help="Show all fields")
    parser.add_argument("--memory-dir", default=MEMORY_DIR,
                        help="Memory directory (default: /home/grace/memory)")
    args = parser.parse_args()

    MEMORY_DIR = args.memory_dir

    tail = None if args.all else args.tail

    if args.search:
        print(f"\n{YELLOW}Searching all stores for: '{args.search}'{RESET}")
        for name, filename in STORES.items():
            entries = load(filename)
            q = args.search.lower()
            hits = [e for e in entries if q in json.dumps(e).lower()]
            if hits:
                show_store(name, filename, search=args.search,
                           tail=tail, verbose=args.verbose)
    elif args.db:
        if args.db not in STORES:
            print(f"{RED}Unknown store '{args.db}'. "
                  f"Choose from: {', '.join(STORES.keys())}{RESET}")
            sys.exit(1)
        show_store(args.db, STORES[args.db],
                   tail=tail, verbose=args.verbose)
    else:
        show_summary()


if __name__ == "__main__":
    main()