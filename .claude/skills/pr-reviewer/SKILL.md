---
name: pr-reviewer
description: Perform a real, published code review on a GitHub pull request using the gh CLI — not just a console summary. Use this skill whenever the user explicitly asks to review a pull request / PR on GitHub (e.g. "review this PR", "راجع هذا الـ PR", "do a code review on PR #123", "check this pull request and leave comments"). The skill fetches the PR diff and metadata, analyzes correctness, security, performance, style, and test coverage, reviews whether the PR title is accurate/clear and matches the repo's naming convention (suggesting alternatives if not), then PUBLISHES the review directly to GitHub as inline comments plus a submitted review (APPROVE / REQUEST_CHANGES / COMMENT) via `gh api` — it does not just print findings to the console. After publishing, it offers (never assumes) to auto-fix the flagged issues by opening a separate follow-up PR targeting the original PR's branch. Requires the gh CLI to be installed and authenticated (gh auth status) with a token that has repo write / pull-request write scope. Do not trigger this skill just because a PR link or number is mentioned in passing (e.g. "PR #123 depends on the other one") — only trigger on an explicit request to review, audit, or leave feedback on a PR.
---

# PR Reviewer (GitHub, live-publishing)

Perform a thorough code review of a GitHub pull request and **publish it directly to GitHub** — inline comments on specific lines, plus a submitted review with a real state (APPROVE / REQUEST_CHANGES / COMMENT). This is not a console-only report: the end result must be visible on the PR's "Files changed" and "Conversation" tabs on GitHub, the same way CodeRabbit or a human reviewer would leave it.

## Prerequisites check (always do this first)

1. Confirm `gh` is installed and authenticated:

    ```bash
    gh auth status
    ```

    If this fails, stop and tell the user to run `gh auth login` with a token that has `repo` scope (classic) or Pull requests: Read & write (fine-grained), then retry. Do not fall back to printing a review in the console as a silent substitute — ask, don't assume.

2. Identify the repo and PR number. If the user gave a URL, parse `owner/repo` and the PR number from it. If they gave only a number, infer the repo from the current git remote (`gh repo view --json nameWithOwner`) or ask if ambiguous.

3. Check whether the authenticated `gh` identity is the PR author:
    ```bash
    ME=$(gh api user -q .login)
    AUTHOR=$(gh pr view <PR_NUMBER> --repo <owner/repo> --json author -q .author.login)
    ```
    **GitHub does not allow a user to APPROVE or REQUEST_CHANGES on their own pull request** — the API rejects it with "Cannot request changes on your own pull request" / "Can not approve your own pull request." If `ME == AUTHOR`, the verdict in Step 4 must be forced to `COMMENT` regardless of what the analysis would otherwise conclude. Tell the user this upfront (e.g. "You're the PR author, so GitHub only allows a COMMENT-type review from your own account — I'll still flag blocking issues clearly in the summary and inline comments, but the formal state will be COMMENT, not REQUEST_CHANGES.") so they aren't surprised the verdict field doesn't say "changes requested" even though blocking issues exist.
    - Still post all inline comments and still write "🔴 Blocking" in the summary body so the severity is visible — only the formal `event` field is constrained, not the content.
    - If a real REQUEST_CHANGES/APPROVE state is needed, the user must run this under a different account (e.g. a bot/CI account or a teammate's token) — mention this as an option if blocking issues exist.

## Step 1 — Gather context

```bash
# Full PR metadata (author, base/head branches, current review state, existing reviews)
gh pr view <PR_NUMBER> --repo <owner/repo> --json title,body,author,baseRefName,headRefName,additions,deletions,changedFiles,reviews,url

# The diff itself
gh pr diff <PR_NUMBER> --repo <owner/repo>

# List of changed files (needed to map comments to exact file paths)
gh pr view <PR_NUMBER> --repo <owner/repo> --json files
```

Read the diff fully before forming opinions — do not review based on file names alone. For non-trivial PRs, also skim the surrounding file (not just the diff hunk) when you need context to judge whether a change is correct, e.g.:

```bash
gh pr checkout <PR_NUMBER> --repo <owner/repo>
```

(only if you need broader file context; not required for small/focused diffs — you can read enough from the diff hunks alone in that case.)

## Step 2 — Avoid duplicate approvals

Since the user wants to avoid repeat approvals: from the `reviews` field fetched in Step 1, check if there is already a review by the same acting user/bot account with state `APPROVED` **and** no new commits have landed since that review's `submittedAt` (compare against the PR's latest commit date via `gh pr view <PR_NUMBER> --json commits`).

-   If an unchanged-since approval already exists from this reviewer identity: do not submit a second APPROVE. Instead, either skip submission and tell the user "already approved, no new changes since," or if there ARE new commits since that approval, proceed with a fresh review (this is a legitimate re-review, not a duplicate).
-   REQUEST_CHANGES or COMMENT reviews are never treated as "duplicates to avoid" — only redundant identical APPROVEs on unchanged code are skipped.

## Step 3 — Analyze the diff (comprehensive review)

Evaluate every changed hunk against these dimensions. Not every dimension applies to every line — use judgment, but scan for all of them:

-   **Correctness / logic bugs**: off-by-one errors, incorrect conditionals, unhandled edge cases, null/undefined handling, race conditions, incorrect error handling or swallowed exceptions.
-   **Security**: injection risks (SQL, command, XSS), secrets or credentials committed, unsafe deserialization, missing input validation/sanitization, broken auth/authz checks, unsafe use of eval or similar.
-   **Performance**: unnecessary loops/N+1 queries, obvious algorithmic regressions, unbounded memory growth, blocking calls in hot paths.
-   **Style / maintainability**: violations of the codebase's existing conventions (infer from surrounding code, don't impose external style opinions), dead code, overly complex functions that should be split, unclear naming, missing/misleading comments where the logic is non-obvious.
-   **Tests**: new logic without corresponding test coverage, tests that don't actually assert meaningful behavior, missing edge case tests for the bug being fixed.

For each finding, note: exact file path, exact line number (from the diff, right-hand/new-file side), severity (blocking vs. suggestion vs. nitpick), and a concrete, actionable suggestion — not just "this could be better."

Do not invent nitpicks to look thorough. If a PR is genuinely clean, say so — a short, honest review beats a padded one.

## Step 3.5 — Review the PR title

Evaluate the PR title (fetched in Step 1 via `title`) against these criteria:

-   **Accuracy**: does it actually describe what the diff does? A title like "fix bug" on a PR that adds a new feature, or a title that only mentions one of three unrelated changes, needs revision.
-   **Clarity**: is it understandable without opening the PR? Avoid vague titles ("update code", "changes", "fix stuff").
-   **Convention**: check recent merged PR titles in the repo (`gh pr list --repo <owner/repo> --state merged --limit 15 --json title`) to detect a house style (e.g. Conventional Commits like `feat:`/`fix:`/`chore:`, ticket-ID prefixes like `PROJ-123:`, imperative mood, max length). Match whatever convention the repo already uses rather than imposing an external one.
-   **Length**: flag if it's excessively long or truncated/cut off.

If the title is already accurate, clear, and follows the repo's convention, say so briefly and move on — don't manufacture a suggestion for a title that's already fine.

If it needs improvement, propose 2-3 concrete alternative titles (not just "consider making this clearer") that follow the detected convention, and include this as its own subsection in the summary body (see updated format below). Do not rename the PR yourself — title changes go in the review as a suggestion for the author to apply, the same way inline code suggestions aren't auto-applied.

## Step 4 — Decide the review verdict

First check the self-review constraint from the prerequisites: if `ME == AUTHOR`, skip straight to `COMMENT` — GitHub will reject anything else. Otherwise:

-   **REQUEST_CHANGES**: any blocking issue (correctness bug, security issue, broken tests, missing critical test coverage for risky logic).
-   **APPROVE**: no blocking issues. Minor style/nitpick comments can still be left alongside an approval.
-   **COMMENT**: you have feedback/questions but it's not clear-cut enough to block or approve outright (e.g. you need clarification from the author on intent), or the user asked only for feedback without a formal verdict.

State this decision explicitly to the user before publishing, in one line, so they can stop you if they disagree. If the verdict was forced to COMMENT due to self-review, say so explicitly (e.g. "Verdict: COMMENT (forced — you're the PR author; underlying assessment is 🔴 blocking issues found").

## Step 5 — Publish the review to GitHub

Use `gh api` to submit a single review event containing both the summary and all inline comments atomically (preferred over posting comments one by one, since a partial failure otherwise leaves a half-posted review). You need the head commit SHA:

```bash
COMMIT_SHA=$(gh pr view <PR_NUMBER> --repo <owner/repo> --json headRefOid -q .headRefOid)
```

Then build the request body. Save it to a temp JSON file to avoid shell-escaping issues with code snippets in comment bodies:

```bash
cat > /tmp/pr_review.json << 'EOF'
{
  "commit_id": "<COMMIT_SHA>",
  "body": "<overall summary in markdown — see format below>",
  "event": "REQUEST_CHANGES",
  "comments": [
    {
      "path": "src/example.py",
      "line": 42,
      "side": "RIGHT",
      "body": "**Bug:** this comparison uses `==` on floats, which can fail due to precision. Use `math.isclose()` instead."
    }
  ]
}
EOF

gh api \
  --method POST \
  -H "Accept: application/vnd.github+json" \
  "/repos/<owner>/<repo>/pulls/<PR_NUMBER>/reviews" \
  --input /tmp/pr_review.json
```

Notes on this call:

-   `event` must be exactly one of `APPROVE`, `REQUEST_CHANGES`, `COMMENT`.
-   `line` refers to the line number in the new version of the file (right-hand side of the diff); use `"side": "LEFT"` only when commenting on a removed line.
-   For multi-line comments, add `"start_line"` and `"start_side"` alongside `line`/`side`.
-   Omit the `comments` array entirely (or leave it empty) if you have no inline feedback — the summary-only review is still valid.
-   Clean up the temp file after: `rm /tmp/pr_review.json`.

### Summary body format

Keep the top-level `body` concise — it's a summary, not a repeat of every inline comment:

```markdown
## Review summary

<1-3 sentence overall assessment>

**Verdict:** <Approve ✅ / Changes requested 🔴 / Comment 💬>

### Title

<Either: "Title is clear and accurate — no changes needed." OR flag the issue + suggested alternatives:>

-   Current: `<existing title>`
-   Suggested: `<alt 1>` / `<alt 2>` / `<alt 3>`

### Highlights

-   <what's good, briefly>

### Issues found

-   🔴 Blocking: <count> — see inline comments
-   🟡 Suggestions: <count>

<Any cross-cutting concern that doesn't map to a single line, e.g. "consider adding an integration test for the new endpoint">
```

## Step 6 — Confirm to the user

After the `gh api` call succeeds, report back with:

-   The verdict submitted (APPROVE / REQUEST_CHANGES / COMMENT).
-   Count of inline comments posted.
-   The PR URL so they can view it directly on GitHub.

If the `gh api` call fails (permissions, invalid line numbers because the diff hunk context changed, etc.), show the actual error — don't silently fall back to printing the review in the console only. Common causes:

-   `line` doesn't fall within the diff's addressable range — GitHub only allows commenting on lines that appear in the diff hunk.
-   `"Cannot request changes on your own pull request"` / `"Can not approve your own pull request"` — this means the self-review check in the prerequisites was missed or the identity changed mid-session; re-check `ME` vs `AUTHOR` and retry with `event: "COMMENT"`.

Diagnose and retry, or ask the user how to proceed.

## Step 7 — Offer to auto-fix (optional, only after publishing)

After Step 6's confirmation, if the review found any 🔴 blocking or 🟡 suggestion-level issues (i.e. there's actually something to fix), ask the user — do not do this unprompted and do not assume yes:

> "Want me to apply fixes for the issues found? I'll create a new branch and open a separate PR with the fixes rather than pushing directly to this PR's branch."

Wait for explicit confirmation (e.g. "yes", "تمام", "go ahead") before touching any code. If the user declines or doesn't respond affirmatively, stop here — the published review is the deliverable.

**Never push fixes directly to the original PR's branch**, even if technically possible (you may not own that branch, and silently rewriting someone else's PR is surprising and can conflict with work in progress). Always work through a new branch and a new PR that the original author can review and merge into their branch, or that maintainers can merge separately.

### 7a — Set up the fix branch

```bash
gh pr checkout <PR_NUMBER> --repo <owner/repo>
git checkout -b fix/pr-<PR_NUMBER>-review-fixes
```

If checkout fails because the PR branch is on a fork you can't push to directly, tell the user and ask whether they want the fixes as a patch/diff instead of a live branch — don't silently give up.

### 7b — Apply fixes

Go through the findings from Step 3 (and the title from Step 3.5, only if the user's "yes" clearly covered the title too — ask separately if unclear) one by one:

-   Only fix issues you already flagged in the published review — don't use this step to introduce new, previously-unmentioned changes; that erodes trust in what the review said it would do.
-   For each fix, make the minimal correct change — don't refactor unrelated code while you're in there.
-   If a flagged issue is a judgment call you're not fully confident about (e.g. "consider adding a test for X" where the right test design is ambiguous), implement your best attempt but flag it clearly in the new PR's description as needing author input, rather than silently guessing.
-   If applying a fix would require information you don't have (business logic intent, which of several valid approaches the team prefers), skip it and list it explicitly as "not auto-fixed — needs author input" rather than guessing at intent.
-   Run the project's existing tests/lints if available (check for `package.json` scripts, `Makefile`, `tox.ini`, etc.) after applying fixes, and mention the results — don't claim fixes are verified if you didn't actually run anything.

### 7c — Commit, push, and open the new PR

```bash
git add -A
git commit -m "fix: address review feedback from PR #<PR_NUMBER>"
git push -u origin fix/pr-<PR_NUMBER>-review-fixes

gh pr create \
  --repo <owner/repo> \
  --base <original PR's head branch, NOT the base branch — this PR should target the original PR's branch so it merges into it> \
  --title "Fix review feedback for #<PR_NUMBER>" \
  --body "$(cat <<'EOF'
Addresses feedback from the review on #<PR_NUMBER>.

### Fixed
- <issue 1 — brief description, referencing the file/line>
- <issue 2>

### Not auto-fixed (needs author input)
- <anything skipped and why>
EOF
)"
```

Note the `--base` here is deliberately the **original PR's branch**, not `main`/`master` — this new PR is meant to feed into the PR being reviewed, so the author can merge it into their own branch and pick up the fixes, rather than fixes landing independently.

### 7d — Report back

Give the user the new PR's URL, a short list of what was fixed vs. skipped, and the test/lint run results from 7b. If nothing meaningful ended up fixed (e.g. everything required author input), say so plainly instead of opening an empty PR.

## What NOT to do

-   Don't just print the review as markdown in the chat and call it done — the review must be posted via `gh api`/`gh pr review` and visible on GitHub.
-   Don't submit one `gh api` call per inline comment — batch them into the single review submission call in Step 5 so the review appears atomically.
-   Don't approve a PR with known blocking issues to be "nice." If there are blocking issues, the verdict is REQUEST_CHANGES regardless of tone.
-   Don't re-approve unchanged code that this reviewer identity already approved (see Step 2).
-   Don't comment on lines outside the diff (GitHub's API will reject it) — only lines actually present in the diff hunks are valid targets for `line`/`start_line`.
-   Don't attempt APPROVE or REQUEST_CHANGES when the authenticated `gh` identity is the PR author — GitHub rejects both; use COMMENT and surface severity in the text instead.
-   Don't apply fixes without an explicit "yes" from the user after the review is published — Step 7 is opt-in, never automatic.
-   Don't push fixes directly to the original PR's branch — always use a new branch/PR targeting the original PR's branch.
-   Don't fix issues that weren't part of the published review, and don't silently guess at ambiguous intent — list those as needing author input instead.
