# Mac mini Daily Lottery Automation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Run the daily lottery once for each of two accounts at 04:00 Mac mini local time, using separate Chrome profiles authenticated on the Mac mini.

**Architecture:** A small Python runner uses Playwright persistent Chrome profiles, one per account, and checks that the account is logged in and the daily draw is explicitly free and available before clicking once. A private per-account marker prevents a second click on the same Mac mini local date. A per-user macOS LaunchAgent runs the runner daily at 04:00; session data stays in the corresponding local browser profile and is never exported from the MacBook.

**Tech Stack:** macOS SSH, Python 3.9 virtual environment, Playwright, Google Chrome, `unittest`, `launchd`.

**Spec:** User request in this conversation; no separate spec file. The target is `https://api.qinggekeji.top/lottery`.

## Global Constraints

- The target URL is `https://api.qinggekeji.top/lottery`.
- Run daily at 04:00 in the Mac mini user's local timezone.
- Operate two accounts in two isolated Chrome profiles on the Mac mini.
- Never export, copy, or transmit Safari/Chrome cookies or other session credentials from the MacBook.
- The user manually signs in to each account in its Mac mini profile before scheduling.
- Click only when the page confirms the daily draw is available and free; stop rather than click if a fee, credit cost, or unclear confirmation appears.
- Keep the Mac mini awake and the user logged in for the scheduled run; keep profile directories private and never log credentials or page storage.

## Review Focus

- Expired or missing login: detect it and do not attempt a draw; test in Task 1.
- Already-claimed daily draw: do not click again; test in Task 1.
- Paid or ambiguous draw: refuse to click and report the blocked status; test in Task 1.
- Account isolation: each account must use only its own persistent profile; verify both identities in Task 2.
- LaunchAgent timing and sleep: confirm 04:00 local scheduling and that the Mac mini is awake; verify the plist and manually run the scheduled command in Task 3.

---

### Task 1: Build and test the two-profile lottery runner

**Files:**
- Create on Mac mini: `~/Library/Application Support/QingkeDailyLottery/requirements.txt`
- Create on Mac mini: `~/Library/Application Support/QingkeDailyLottery/run.py`
- Create on Mac mini: `~/Library/Application Support/QingkeDailyLottery/test_run.py`
- Create on Mac mini: `~/Library/Application Support/QingkeDailyLottery/.venv/`
- Create on Mac mini at runtime: `~/Library/Application Support/QingkeDailyLottery/profiles/account-1/` and `account-2/`
- Create on Mac mini at runtime: `~/Library/Logs/QingkeDailyLottery/`

**Interfaces:**
- Consumes: the target URL and the user's two accounts.
- Produces: `run_account(profile_dir, mode)`, where `mode` is `"setup"` or `"daily"` and the result is one of `"drawn"`, `"unavailable"`, `"login-required"`, or `"blocked"`; `run_daily_lottery()` runs both profile directories sequentially and reports each result without printing session data.

- [x] **Step 1: Write focused behavior tests** for `run_account`: a logged-out profile does not click; an unavailable/disabled draw does not click; an available free draw is eligible for one click; a same-day attempt cannot click again; a paid or ambiguous draw does not click; each account uses a different profile directory.
- [ ] **Step 2: Run tests to verify they fail.** Run `"$HOME/Library/Application Support/QingkeDailyLottery/.venv/bin/python" -m unittest discover -s "$HOME/Library/Application Support/QingkeDailyLottery"`. Expected: the tests fail because the runner is not implemented.
- [x] **Step 3: Implement the runner** in `run.py` using two private persistent Chrome profile directories. In `"setup"` mode, open the target page for manual sign-in without drawing. In `"daily"` mode, use observed accessible page controls and explicit page state to detect login, availability, free status, and completion; never guess a control or retry a draw when its outcome is uncertain.
- [x] **Step 4: Run tests to verify they pass.** Run `"$HOME/Library/Application Support/QingkeDailyLottery/.venv/bin/python" -m unittest discover -s "$HOME/Library/Application Support/QingkeDailyLottery"`. Expected: all tests pass, and the test runner creates no real draw or credential data.
- [x] **Step 5: Keep runner files local to the Mac mini**; do not copy profile directories, logs, or credentials into source control.

### Task 2: Authenticate and verify both isolated profiles

**Files:**
- Use on Mac mini: `~/Library/Application Support/QingkeDailyLottery/profiles/account-1/`
- Use on Mac mini: `~/Library/Application Support/QingkeDailyLottery/profiles/account-2/`

**Interfaces:**
- Consumes: Task 1's `run_account(profile_dir, "setup")` and `run_daily_lottery()`.
- Produces: two locally authenticated profiles, each verified against its intended account, and one observed daily draw result per account.

- [x] **Step 1: Launch setup mode for account 1 and account 2 separately;** manually sign in to the intended account in each Chrome window. Do not copy browser data from the MacBook.
- [x] **Step 2: Verify account isolation** by checking that each profile displays the intended account identity and that the two identities differ.
- [ ] **Step 3: Verify the site's automation terms and the draw's cost/confirmation state.** If automated draws are disallowed, or the draw is not clearly free and available, stop without scheduling.
- [x] **Step 4: Run one manual daily-mode smoke test** for each account; if the draw button is disabled, verify the result is `"unavailable"` and no click occurs. Only test an actual draw when the page marks the free daily draw available; verify one click at most.

### Task 3: Schedule the runner at 04:00

**Files:**
- Create on Mac mini: `~/Library/LaunchAgents/top.qingke.daily-lottery.plist`
- Write logs on Mac mini: `~/Library/Logs/QingkeDailyLottery/`

**Interfaces:**
- Consumes: Task 1's `run_daily_lottery()` and Task 2's verified profiles.
- Produces: a per-user LaunchAgent scheduled daily at 04:00 local time.

- [x] **Step 1: Create the LaunchAgent plist** with `StartCalendarInterval` set to hour `4` and minute `0`, using absolute paths for the virtual environment's Python interpreter, the runner, and log files; do not enable `RunAtLoad`.
- [x] **Step 2: Validate and load the LaunchAgent.** Run `plutil -lint "$HOME/Library/LaunchAgents/top.qingke.daily-lottery.plist"` and bootstrap it with `launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/top.qingke.daily-lottery.plist"`. Expected: the plist is valid and `launchctl print "gui/$(id -u)/top.qingke.daily-lottery"` shows the loaded job and its 04:00 calendar interval.
- [x] **Step 3: Run the scheduled command manually once** and inspect the non-sensitive per-account result logs. Expected: each account is drawn at most once, disabled draws are reported as unavailable, and errors such as login expiration or ambiguous cost are reported without a click.
- [x] **Step 4: Confirm the Mac mini stays awake with the user session logged in at 04:00;** document that a sleeping or logged-out Mac cannot guarantee the scheduled run.
