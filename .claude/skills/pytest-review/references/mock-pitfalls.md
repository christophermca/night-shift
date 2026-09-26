# unittest.mock pitfalls that make tests lie

Each entry: **symptom** (what to look for), **why** it lies, **detect**, **fix**.
Examples are real ones found while reviewing the night-shift repo.

## Contents
1. Asserting on auto-created attributes
2. Mock shape ≠ real shape
3. Loose MagicMock hides missing methods
4. Patching where defined, not where looked up
5. Stacked / class-level `@patch` argument order
6. Partial patching still touches the machine
7. Module-level caches leak between tests
8. Smoke tests and tests that can't reach the code
9. xfail that fails for the wrong reason

---

## 1. Asserting on auto-created attributes
**Symptom:** `assert something.return_value`, `assert mock.foo`, `assert result`
where `result` came from a mock.
**Why:** A `MagicMock` creates any attribute on access and it is always truthy.
`module._settings().return_value` is a brand-new MagicMock, so
`assert settings` passes no matter what `_settings()` did.
**Detect:** Mutation check — change the production call's arguments; the test stays green.
**Fix:** Assert identity and arguments:
```python
settings = module._settings()
assert settings is mock_new_full.return_value
mock_new_full.assert_called_once_with(source.lookup.return_value, None, None)
```

## 2. Mock shape ≠ real shape
**Symptom:** Production does `Settings()()` (wrapper whose `__call__` returns the
real object) but the test sets `mock_cls.return_value = fake`.
**Why:** The test exercises code you didn't write. Here the production line was
`settings = Settings()` → `AttributeError: 'Settings' object has no attribute
'get_value'` on the first real run, while the suite was green at 100% coverage.
**Detect:** Run the real code path unmocked (SKILL.md step 3). `create_autospec(Settings)`
would also raise `Mock object has no attribute 'get_value'`.
**Fix:** Mirror each call level: `mock_cls.return_value.return_value = fake`,
or use `create_autospec(RealClass)` so a wrong shape raises.

## 3. Loose MagicMock hides missing methods
**Symptom:** Code calls a method name the real API doesn't have
(`settings.set_bool` — Gio only has `set_boolean`), or a check like
`callable(proc)` that is always True for a MagicMock but False for a real `Popen`.
**Why:** MagicMock accepts any name and is callable.
**Fix:** `MagicMock(spec=Gio.Settings)` restricts attributes to the real class.
For an *instance* use `create_autospec(Cls, instance=True)` — a spec taken from a
class is itself callable, so `MagicMock(spec=Popen)` still passes `callable()`.
If the test patches the very thing you want to spec (e.g. `subprocess.Popen`),
capture the real one at import time: `REAL_POPEN = subprocess.Popen`.

## 4. Patching where defined, not where looked up
**Symptom:** `@patch("pkg.bin.fetch.Fetcher")` but the code under test did
`from pkg.bin.fetch import Fetcher` in `pkg/__init__.py`.
**Why:** `patch` rebinds one name in one namespace; the importer already holds
its own reference. (Unlike `jest.mock`, which swaps the module in the registry.)
**Fix:** Patch `<module that uses it>.<name it uses>` — e.g. `pkg.Fetcher`.
For `import requests` + `requests.get(...)`, patch `pkg.mod.requests.get`.

## 5. Stacked / class-level `@patch` argument order
**Symptom:** A test class decorated with two `@patch`es whose methods name only
one mock, or name them in the wrong order.
**Why:** Decorators apply bottom-up → the **bottom** patch is the **first**
argument after `self`. *Every* method receives all patch mocks positionally,
regardless of parameter names; fixtures are injected by name only *after* them.
So `def test_x(self, mock_a, mock_settings)` may bind `mock_settings` to the
second patch, silently shadowing the fixture.
**Detect:** Print the mocks' `_mock_name`, or assert on them.
**Fix:** Name all patch args in bottom-up order, or prefer per-test `with patch(...)`.

## 6. Partial patching still touches the machine
**Symptom:** Only the last call in a chain is patched
(`@patch("...Gio.Settings.new_full")`) while earlier calls
(`Gio.SettingsSchemaSource.new_from_directory(~/.local/...)`) run for real.
**Why:** Passes on the author's machine (resource installed), fails in CI/fresh
clone: `GLib.Error: Failed to open file …/gschemas.compiled`.
**Detect:** `HOME=$(mktemp -d) python -m pytest`.
**Fix:** Patch at the seam that owns the resource (`_get_schema_source`, the
module's `Gio`, `requests.get`), or inject paths so tests can pass `tmp_path`.

## 7. Module-level caches leak between tests
**Symptom:** A module global like `_schema_source = None` filled lazily.
**Why:** The first test to run fills it; later tests reuse a real (or stale mock)
object → order-dependent results.
**Fix:** `monkeypatch.setattr(module, "_cache", None)` in the test/fixture
(restored automatically). Check by running the file in a different order.

## 8. Smoke tests and tests that can't reach the code
**Symptom:** No assert; or an error injected into a mock that the chosen
arguments never call (e.g. `side_effect = HTTPError` on `_get_location` while
`use_geoclue=False`, and the HTTP method itself is mocked out).
**Why:** Passes forever, proves nothing.
**Fix:** Inject the failure where the real one originates
(`response.raise_for_status.side_effect = HTTPError(...)`) and assert the
observable outcome (`returns None`, `set_value.assert_not_called()`).

## 9. xfail that fails for the wrong reason
**Symptom:** `@pytest.mark.xfail` without `raises=`, or a mock set up so the test
errors before reaching the buggy line.
**Why:** Shows as the expected `x` even though it's not exercising the bug.
**Detect:** `pytest --runxfail -q | grep "^E "` — each failure message should name the bug.
**Fix:** Add `strict=True` and `raises=<ExpectedExc>`; fix the setup until the
failure is the bug itself. When a strict xfail XPASSes, either the bug is fixed
(remove the marker) or your hypothesis was wrong (turn it into a normal
regression test).
