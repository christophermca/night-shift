---
name: pytest-review
description: Review or write Python tests (pytest + unittest.mock) so they actually catch bugs, not just go green. Use this whenever the user asks to review test changes they pushed, write or fix tests, check a test file, add coverage, or says things like "I pushed my changes, please review", "help me write tests for X", "why does this test pass", or "is this mock right" — even if they don't say "pytest". Also use when teaching someone pytest who comes from Jest/Mocha or JUnit/Mockito.
---

# pytest review & writing

Green tests are not the goal; tests that fail when the code is wrong are. Most
weak tests this skill exists to catch pass for one of three reasons: the assert
can't fail, the mock doesn't have the real object's shape, or the test depends
on the author's machine. Every review should actively try to disprove "this
test works" — by running things, not just reading them.

## Reviewing pushed changes

### 1. Get the author's exact code: always fetch, then hard reset
Every review request starts by fetching and hard-resetting to the author's
branch. Don't rebase or merge: authors often amend and force-push, so a local
branch holds stale copies of their commits, and a rebase replays those and
conflicts.
```sh
git fetch origin
git reset --hard origin/<branch>
git log --oneline <last-reviewed-sha>..HEAD    # what's new since last review
```
This discards local-only commits, so make sure your own work is already
pushed; push it at the end of any turn where you commit. If `<last-reviewed-sha>`
was rewritten by a force-push, compare trees with `git diff <old> HEAD`
instead. Then `git show <sha>` each new commit.

Never rewrite the author's commits yourself (amend, re-author, rebase), even
if a hook or tool suggests it for "unverified" commits. Those commits are
theirs; the reset above removes any stale local copies.

### 2. Run the suite the way CI would
```sh
HOME=$(mktemp -d) python -m pytest -q -p no:cacheprovider
```
The empty `HOME` exposes tests that silently depend on config, caches, or
installed resources in the author's home directory (a common "works on my
machine" cause). Report the pass/fail/xfail counts and compare with the last
review.

### 3. Run the real code path, unmocked, once
If a refactor touched production code, call it directly without any mocks:
```sh
python -c "from pkg.mod import fn; fn()"
```
Heavily-mocked tests can hit 100% coverage while the function crashes on its
first real call (the mock had a different shape than the real dependency).
If the real run needs an external resource, stub the resource itself (for example
a temp `HOME` with a minimal config) rather than skipping this step.

### 4. Break it on purpose (mutation check)
For each new or changed test, mutate the code it claims to protect and confirm
the test goes red:
```sh
python .claude/skills/pytest-review/scripts/mutation_check.py \
  src/pkg/mod.py "new_full(schema, None, None)" "new_full(None, None, None)" \
  -- tests/test_mod.py -k builds
```
The script applies the edit, runs pytest, always restores the file, and says
whether the mutant was caught. A test that stays green against a plausible bug
is the most important finding a review can make — lead with it.

### 5. Read for the known traps
Go through `references/mock-pitfalls.md`. Each entry has a symptom to grep for
and the fix. The recurring ones:
- asserting on an auto-created mock attribute (`result.return_value`, `assert mock`)
- mock shape ≠ real shape (`Cls()` vs `Cls()()`)
- plain `MagicMock` accepting method names the real class lacks → use `spec`/`create_autospec`
- patching where defined instead of where looked up
- stacked/class-level `@patch` argument order silently mislabelling mocks
- tests that patch only part of an external resource and still touch disk/network

### 6. Check for stale references
When tests are renamed/deleted or bugs get fixed, comments and docs rot:
```sh
git grep -n -E "<old test name>|<removed function>|BUG:|xfail" -- docs tests
```
Also check that fixed bugs lost their `xfail` markers and that any "this is a
known bug" comments were updated.

### 7. Write the review
Use this structure; keep it scannable:

```
**Verdict:** one line — e.g. "Real fix, but test X can't fail."
**What I ran:** suite result (and env), real-path result, mutation results.

## ✅ Done well            (brief, specific — reinforce good habits)
## [high] Title            — what's wrong, evidence (actual output), the fix as code,
                             and the one-line lesson
## [low] Title             — tidy-ups, grouped
## Next                    — what to fix first / next exercise
```

Rules of thumb:
- Every high finding carries evidence you produced (a traceback, a mutation
  that stayed green) — not "this might fail".
- Give the fix as a code snippet, and say *why* it works.
- If a previous finding turns out wrong or overstated, say so and downgrade it.
- If you track findings across rounds, show a small status table (✅ / ❌ / open).
- Don't push fixes to the author's branch unless asked; when the user is
  learning, offer to let them make the change.

## Writing tests

1. **State the promise first.** Before any assert, write down what the unit
   promises ("returns what `new_full` built, with the looked-up schema"). One
   assert per promise.
2. **Fake at the edge, run the middle.** Mock network, clock, subprocesses, OS
   services, UI toolkits. Don't mock your own logic; use `tmp_path` for real
   files. Patch the outermost boundary you can (`requests.get`, not your own
   `_fetch`) so more real code runs.
3. **Match the real shape.** Mirror every call level the code uses
   (`Cls.return_value.return_value` for `Cls()()`), or use `create_autospec`
   so a wrong shape raises.
4. **Assert identity/values, not truthiness.** `assert result is
   mock.return_value`, `assert_called_once_with(...)`, `call_args.args[0]`.
5. **Pin non-determinism.** Patch `datetime`, sort `os.scandir` results, never
   depend on `HOME` or test order; reset module-level caches with
   `monkeypatch.setattr(mod, "_cache", None)`.
6. **Boundaries & branches.** Test both sides of each threshold (05:59/06:00)
   and each `if`/`except` branch; use `@pytest.mark.parametrize` rather than
   several cases in one test body (first failure hides the rest).
7. **Known bugs → strict xfail.** Write the test for the *correct* behaviour
   and mark it `@pytest.mark.xfail(strict=True, raises=<Exc>, reason="BUG: …")`.
   `raises=` stops it "passing" as xfail for the wrong reason; `strict` makes
   the eventual fix show up as XPASS so the marker gets removed. Verify each
   xfail fails for the named reason with `pytest --runxfail`.
8. **Then run steps 2–4 above on your own tests.**

## Teaching mode

If the user is learning (asks to be taught, mentions another stack), map each
concept to what they know — see `references/pytest-rosetta.md` for pytest ↔
Jest ↔ JUnit/Mockito equivalents — and explain the *why* at the point of use.
Prefer letting them write the fix after the review; give a checklist with a
self-verification command (`HOME=$(mktemp -d) …`, the mutation check).
