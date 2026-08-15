"""
vault_cli.py — Interactive CLI for VAULT.

Usage:
    python vault_cli.py

Features:
  • First run: set a master password and initialize the vault.
  • Subsequent runs: unlock with master password → full CRUD session.
  • Password copy to clipboard via pyperclip (no password ever printed
    unless the user explicitly chooses "reveal").
  • Auto-logout warning after 5 minutes of idle time.

pyperclip requires a clipboard back-end:
  Windows  — built-in (no extra install)
  macOS    — built-in (pbcopy/pbpaste)
  Linux    — install xclip or xsel:  sudo apt install xclip
"""

import os
import sys
import time
import getpass
import threading

# Ensure sibling modules resolve when run directly from any cwd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import pyperclip
    _CLIPBOARD_AVAILABLE = True
except ImportError:
    _CLIPBOARD_AVAILABLE = False

from vault_store import (
    VaultStore,
    VaultNotInitializedError,
    WrongMasterPasswordError,
    EntryNotFoundError,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

_VAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vault.json")
_SESSION_TTL = 300  # 5 minutes, matches server + frontend

# ANSI colour helpers (disabled automatically on Windows cmd without ANSI support)
_USE_COLOR = sys.stdout.isatty() and os.name != "nt" or (
    os.name == "nt" and os.environ.get("WT_SESSION")  # Windows Terminal supports ANSI
)


def _c(code: str, text: str) -> str:
    if not _USE_COLOR:
        return text
    codes = {
        "bold":    "\033[1m",
        "dim":     "\033[2m",
        "green":   "\033[92m",
        "yellow":  "\033[93m",
        "red":     "\033[91m",
        "cyan":    "\033[96m",
        "brass":   "\033[33m",
        "reset":   "\033[0m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


def _hr() -> None:
    print(_c("dim", "─" * 52))


def _banner() -> None:
    print()
    print(_c("brass", "  ██╗   ██╗ █████╗ ██╗   ██╗██╗  ████████╗"))
    print(_c("brass", "  ██║   ██║██╔══██╗██║   ██║██║  ╚══██╔══╝"))
    print(_c("brass", "  ██║   ██║███████║██║   ██║██║     ██║   "))
    print(_c("brass", "  ╚██╗ ██╔╝██╔══██║██║   ██║██║     ██║   "))
    print(_c("brass", "   ╚████╔╝ ██║  ██║╚██████╔╝███████╗██║   "))
    print(_c("brass", "    ╚═══╝  ╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝   "))
    print()
    print(_c("dim", "  Encrypted password manager  ·  local vault.json"))
    print()


# ---------------------------------------------------------------------------
# Idle timer
# ---------------------------------------------------------------------------

class IdleTimer:
    """Fires a callback after `ttl` seconds of inactivity."""

    def __init__(self, ttl: int, callback) -> None:
        self._ttl = ttl
        self._callback = callback
        self._lock = threading.Lock()
        self._last_active = time.monotonic()
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def reset(self) -> None:
        with self._lock:
            self._last_active = time.monotonic()

    def stop(self) -> None:
        with self._lock:
            self._running = False

    def _loop(self) -> None:
        while True:
            time.sleep(5)
            with self._lock:
                if not self._running:
                    return
                elapsed = time.monotonic() - self._last_active
            if elapsed >= self._ttl:
                self._callback()
                return


# ---------------------------------------------------------------------------
# CLI session
# ---------------------------------------------------------------------------

class VaultCLI:
    def __init__(self) -> None:
        self._store = VaultStore(vault_path=_VAULT_PATH)
        self._master_password: str | None = None
        self._timer: IdleTimer | None = None

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _activity(self) -> None:
        """Call on every user interaction to reset the idle timer."""
        if self._timer:
            self._timer.reset()

    def _auto_logout(self) -> None:
        print()
        print(_c("yellow", "\n  ⏱  Auto-logout: 5 minutes of inactivity. Vault sealed."))
        self._master_password = None
        # Re-enter the lock screen by raising so the REPL exits cleanly
        os._exit(0)

    def _start_timer(self) -> None:
        if self._timer:
            self._timer.stop()
        self._timer = IdleTimer(_SESSION_TTL, self._auto_logout)

    def _stop_timer(self) -> None:
        if self._timer:
            self._timer.stop()
            self._timer = None

    def _prompt(self, text: str) -> str:
        self._activity()
        return input(text).strip()

    def _secure_prompt(self, text: str) -> str:
        self._activity()
        return getpass.getpass(text)

    def _copy_to_clipboard(self, text: str) -> bool:
        if not _CLIPBOARD_AVAILABLE:
            return False
        try:
            pyperclip.copy(text)
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Setup / unlock
    # ------------------------------------------------------------------

    def run(self) -> None:
        _banner()
        if not self._store.is_initialized():
            self._setup_flow()
        else:
            self._unlock_flow()

    def _setup_flow(self) -> None:
        print(_c("cyan", "  No vault found. Let's create one."))
        print(_c("dim",  "  Your master password encrypts everything."))
        print(_c("dim",  "  It is never stored — only a hash is saved."))
        print()
        while True:
            pw = self._secure_prompt("  Choose master password (min 8 chars): ")
            if len(pw) < 8:
                print(_c("red", "  ✗ Too short. Pick something longer."))
                continue
            confirm = self._secure_prompt("  Confirm master password: ")
            if pw != confirm:
                print(_c("red", "  ✗ Passwords don't match. Try again."))
                continue
            break

        self._store.initialize(pw)
        self._master_password = pw
        print(_c("green", "  ✔ Vault created and sealed with your master password."))
        print()
        self._start_timer()
        self._main_menu()

    def _unlock_flow(self) -> None:
        print(_c("cyan", "  Vault found. Enter your master password to unlock."))
        print()
        attempts = 0
        while attempts < 5:
            pw = self._secure_prompt("  Master password: ")
            if self._store.verify_master_password(pw):
                self._master_password = pw
                print(_c("green", "  ✔ Vault unlocked."))
                print()
                self._start_timer()
                self._main_menu()
                return
            attempts += 1
            remaining = 5 - attempts
            print(_c("red", f"  ✗ Incorrect password. {remaining} attempt(s) remaining."))

        print(_c("red", "  ✗ Too many failed attempts. Exiting."))
        sys.exit(1)

    # ------------------------------------------------------------------
    # Main menu
    # ------------------------------------------------------------------

    def _main_menu(self) -> None:
        while True:
            _hr()
            print(_c("bold", "  VAULT — main menu"))
            _hr()
            print("  [1] List all sites")
            print("  [2] Search by site name")
            print("  [3] Add a new entry")
            print("  [4] Copy password to clipboard")
            print("  [5] Reveal a password")
            print("  [6] Delete an entry")
            print("  [7] Lock vault (logout)")
            print("  [q] Quit")
            _hr()

            choice = self._prompt("  Choose: ")

            if choice == "1":
                self._cmd_list_sites()
            elif choice == "2":
                self._cmd_search()
            elif choice == "3":
                self._cmd_add()
            elif choice == "4":
                self._cmd_copy()
            elif choice == "5":
                self._cmd_reveal()
            elif choice == "6":
                self._cmd_delete()
            elif choice == "7":
                self._cmd_lock()
                return
            elif choice.lower() == "q":
                self._cmd_lock()
                print(_c("dim", "  Goodbye."))
                return
            else:
                print(_c("yellow", "  Unknown option."))

    # ------------------------------------------------------------------
    # Commands
    # ------------------------------------------------------------------

    def _cmd_list_sites(self) -> None:
        sites = self._store.list_sites(self._master_password)
        if not sites:
            print(_c("dim", "\n  Vault is empty.\n"))
            return
        print()
        for i, s in enumerate(sites, 1):
            print(f"  {_c('brass', str(i).rjust(3))}  {s['site']}  {_c('dim', s['id'][:8] + '…')}")
        print()

    def _cmd_search(self) -> None:
        query = self._prompt("  Search site name: ")
        if not query:
            return
        results = self._store.search_entries(self._master_password, query)
        if not results:
            print(_c("yellow", f"\n  No entries matching '{query}'.\n"))
            return
        print()
        for entry in results:
            print(f"  {_c('brass', '→')} {_c('bold', entry['site'])}")
            print(f"     user: {entry['username']}")
            print(f"     id:   {_c('dim', entry['id'])}")
        print()

    def _cmd_add(self) -> None:
        print()
        site     = self._prompt("  Website (e.g. github.com): ")
        username = self._prompt("  Username: ")
        password = self._secure_prompt("  Password (hidden): ")
        if not site or not username or not password:
            print(_c("red", "  ✗ All fields required."))
            return

        entry_id = self._store.add_entry(self._master_password, site, username, password)
        print(_c("green", f"  ✔ Entry saved [{entry_id[:8]}…]"))

        if _CLIPBOARD_AVAILABLE:
            answer = self._prompt("  Copy password to clipboard? [y/N]: ")
            if answer.lower() == "y":
                if self._copy_to_clipboard(password):
                    print(_c("green", "  ✔ Copied."))
        print()

    def _cmd_copy(self) -> None:
        if not _CLIPBOARD_AVAILABLE:
            print(_c("red", "\n  pyperclip not installed. Run: pip install pyperclip\n"))
            return
        query = self._prompt("  Site name to copy password for: ")
        if not query:
            return
        results = self._store.search_entries(self._master_password, query)
        if not results:
            print(_c("yellow", f"\n  No entries matching '{query}'.\n"))
            return

        entry = self._pick_entry(results)
        if entry is None:
            return

        if self._copy_to_clipboard(entry["password"]):
            print(_c("green", f"  ✔ Password for {entry['site']} copied to clipboard."))
        else:
            print(_c("red", "  ✗ Clipboard copy failed."))
        print()

    def _cmd_reveal(self) -> None:
        query = self._prompt("  Site name to reveal: ")
        if not query:
            return
        results = self._store.search_entries(self._master_password, query)
        if not results:
            print(_c("yellow", f"\n  No entries matching '{query}'.\n"))
            return

        entry = self._pick_entry(results)
        if entry is None:
            return

        print()
        print(f"  site:     {_c('bold', entry['site'])}")
        print(f"  username: {entry['username']}")
        print(f"  password: {_c('yellow', entry['password'])}")
        print()

        # Auto-clear hint
        print(_c("dim", "  (Clear your terminal when done: cls / clear)"))
        print()

    def _cmd_delete(self) -> None:
        query = self._prompt("  Site name to delete: ")
        if not query:
            return
        results = self._store.search_entries(self._master_password, query)
        if not results:
            print(_c("yellow", f"\n  No entries matching '{query}'.\n"))
            return

        entry = self._pick_entry(results)
        if entry is None:
            return

        confirm = self._prompt(
            f"  Delete '{entry['site']}' ({entry['username']})? Type YES to confirm: "
        )
        if confirm == "YES":
            self._store.delete_entry(self._master_password, entry["id"])
            print(_c("green", "  ✔ Entry deleted."))
        else:
            print(_c("dim", "  Cancelled."))
        print()

    def _cmd_lock(self) -> None:
        self._stop_timer()
        self._master_password = None
        print(_c("cyan", "\n  Vault locked. Goodbye.\n"))

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _pick_entry(self, results: list[dict]) -> dict | None:
        """If multiple results, ask the user which one. Returns None on cancel."""
        if len(results) == 1:
            return results[0]

        print()
        for i, e in enumerate(results, 1):
            print(f"  [{i}] {e['site']}  ({e['username']})")
        choice = self._prompt("  Pick number (or Enter to cancel): ")
        if not choice:
            return None
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
        except ValueError:
            pass
        print(_c("yellow", "  Invalid choice."))
        return None


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    try:
        cli = VaultCLI()
        cli.run()
    except KeyboardInterrupt:
        print(_c("dim", "\n\n  Interrupted. Vault sealed."))
        sys.exit(0)
    except (VaultNotInitializedError, WrongMasterPasswordError) as exc:
        print(_c("red", f"\n  Error: {exc}\n"))
        sys.exit(1)


if __name__ == "__main__":
    main()
