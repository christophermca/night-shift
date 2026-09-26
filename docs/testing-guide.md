# Testing night-shift with pytest

A guide to reading the tests, written for someone who already knows Jest/Mocha and JUnit.
The detail is in the tests themselves: every teaching comment starts with `LEARN:`.

```sh
grep -n "LEARN:" tests/*.py      # every lesson, in file order
```

## Running the tests

```sh
python -m pytest                                  # everything, with coverage (from pytest.ini)
python -m pytest tests/test_cli.py                # one file
python -m pytest tests/test_cli.py::test_no_args_prints_help   # one test
python -m pytest -k "symlink"                     # tests whose name matches
python -m pytest -x                               # stop at first failure
python -m pytest -s                               # show print() output
python -m pytest --no-cov                         # skip coverage (quicker to read)
python -m pytest -rx                              # list xfailed tests with their reasons
python -m pytest --runxfail                       # run xfail tests as normal tests, to see why they fail
```

(In the Claude cloud container the working interpreter is `python3.12`, because that's the
version the system's PyGObject was built for. On your machine, use whatever your venv has.)

## How pytest finds tests

| | pytest | Jest | JUnit 5 |
|---|---|---|---|
| Test file | `tests/test_*.py` | `*.test.js` | `*Test.java` |
| Test | any function named `test_*` | `test()` / `it()` | `@Test` method |
| Grouping | `class Test*` (no `__init__`) | `describe()` | test class / `@Nested` |
| Config | `pytest.ini` | `jest.config.js` | build tool |

`pytest.ini` sets `pythonpath = src`. That's why tests can `import night_shift` without
installing the package.

## Rosetta table

| Concept | pytest / `unittest.mock` | Jest | JUnit 5 + Mockito |
|---|---|---|---|
| Assert | `assert x == y` | `expect(x).toBe(y)` | `assertEquals(y, x)` |
| Expect an exception | `with pytest.raises(E, match="msg"):` | `expect(fn).toThrow("msg")` | `assertThrows(E.class, ...)` |
| Setup / teardown | fixture with `yield` | `beforeEach` / `afterEach` | `@BeforeEach` / `@AfterEach` |
| Setup for every test | `@pytest.fixture(autouse=True)` | top-level `beforeEach` | base class `@BeforeEach` |
| Shared across files | `tests/conftest.py` | `setupFilesAfterEnv` | base class / extension |
| Fake object | `MagicMock()` | `jest.fn()` | `mock(Foo.class)` |
| Replace a dependency | `@patch("mod.name")` | `jest.mock("mod")` | `@Mock` + `@InjectMocks` |
| Stub a return | `m.return_value = x` | `m.mockReturnValue(x)` | `when(m.f()).thenReturn(x)` |
| Stub a sequence | `m.side_effect = [a, b]` | `mockReturnValueOnce(a)...` | `thenReturn(a, b)` |
| Stub a throw | `m.side_effect = Err()` | `mockImplementation(() => {throw})` | `thenThrow(new Err())` |
| Stub with logic | `m.side_effect = func` | `mockImplementation(func)` | `thenAnswer(...)` |
| Verify a call | `m.assert_called_once_with(a)` | `toHaveBeenCalledWith(a)` | `verify(m).f(a)` |
| Capture an argument | `m.call_args.args[0]` | `m.mock.calls[0][0]` | `ArgumentCaptor` |
| Type-safe mock | `MagicMock(spec=Cls)` / `create_autospec` | (TypeScript types) | built in |
| Table-driven test | `@pytest.mark.parametrize` | `test.each` | `@ParameterizedTest` |
| Known-broken test | `@pytest.mark.xfail(strict=True)` | `test.failing` | none |
| Temp directory | `tmp_path` fixture | `fs.mkdtemp` yourself | `@TempDir` |
| Capture stdout | `capsys` fixture | `jest.spyOn(console, "log")` | redirect `System.out` |
| Change a global or env var | `monkeypatch` fixture | assign + restore by hand | `@SetEnvironmentVariable` (ext) |

## The #1 gotcha: patch where it's *looked up*

```python
# src/night_shift/__init__.py
from night_shift.bin.get_sunrise_sunset import GetTimeOfSunriseSunset
```

That line copies a reference to the class into the `night_shift` module. So to fake it
for `main()`, you patch **`night_shift.GetTimeOfSunriseSunset`**, not
`night_shift.bin.get_sunrise_sunset.GetTimeOfSunriseSunset`. Patching the original only
changes the original name; `night_shift` still holds the real class.

`jest.mock()` replaces the whole module in the registry before anything imports it, which
is why JS doesn't have this problem. Python's `patch` swaps one name in one namespace
while the code is already running.

Rule of thumb: **patch `<module that uses it>.<name it uses>`**.

## Suggested reading order

1. [`tests/test_is_day_or_night.py`](../tests/test_is_day_or_night.py): plain `assert`,
   fixtures, `@patch` vs `with patch`, faking the clock, boundary values, `xfail`.
2. [`tests/test_settings.py`](../tests/test_settings.py): mocking a whole library (`Gio`),
   `assert_called_once_with`, `call_args`, `side_effect` exceptions, `capsys`.
3. [`tests/test_cli.py`](../tests/test_cli.py): fixtures that depend on fixtures, factory
   fixtures, `monkeypatch`, `yield` teardown, `parametrize`, `return_value` chains.
4. [`tests/test_service.py`](../tests/test_service.py): real temp files with `tmp_path`,
   monkeypatching module globals, asserting side effects, `pytest.raises`, `call()` and
   call order.
5. [`tests/test_get_sunrise_sunset.py`](../tests/test_get_sunrise_sunset.py): `autouse`,
   class-level `@patch` and its argument-order trap, a test that can't fail,
   `side_effect` as a list or a function, and `spec` / `create_autospec` catching real bugs.

## Arrange / Act / Assert

Most tests have three blocks separated by blank lines:

```python
def test_check_now_runs_check(argv):
    argv("--check-now")                          # Arrange: build the situation

    with patch("night_shift.check") as check:
        night_shift.main()                       # Act: do ONE thing

    check.assert_called_once_with()              # Assert: check the outcome
```

If a test needs two "Act" steps, it's usually two tests.

## What to mock (and what not to)

- **Mock** anything slow, non-deterministic or with side effects: the network
  (`requests.get`), the clock (`datetime`), processes (`subprocess`), and system services
  (`Gio`, `systemctl`).
- **Don't mock** things that are cheap and safe to run for real: your own pure logic, and
  files in `tmp_path`. The more real code a test runs, the more it proves.
- **Mock at the edge.** `TestFetchSunriseSunset` mocks `requests.get`, not
  `_get_sunrise_sunset`, so the parsing and saving code actually runs.
- **Use `spec`** at the edges that matter. A plain `MagicMock` accepts any method name,
  which is how the `set_bool` and `callable(agent)` bugs stayed hidden.

## Try it yourself

Each known bug has a strict `xfail` test. To practise the red/green loop:

1. Pick a bug from the table.
2. Run its test with `--runxfail` and read the failure (red).
3. Fix the source.
4. Run again. pytest now reports **XPASS(strict)** as a failure, meaning "you fixed it,
   remove the marker".
5. Delete the `@pytest.mark.xfail(...)` lines and run once more (green).

| Bug | Source | Test |
|---|---|---|
| `_get_schema_source.lookup` is missing `()` | `bin/is_day_or_night.py` | `test_settings` |
| `systemctl enable` is outside the `for` loop | `lib/service.py` `_start_services` | `test_start_services_enables_every_timer` |
| `systemctl disable` is outside the `for` loop | `lib/service.py` `_stop_services` | `test_stop_services_disables_every_timer` |
| `self.units` should be `self.all_units` | `lib/service.py` `_remove_symlink` | `test_destroy_removes_symlinks` |
| `set_bool` should be `set_boolean` | `bin/get_sunrise_sunset.py` `_save` | `test_bool_uses_real_gio_method` |
| `callable(self.agent)` is never true for a Popen | `bin/get_sunrise_sunset.py` `_get_location` | `test_kills_geoclue_agent` |

More exercises:

- Rewrite `test_is_day_or_night_during_day` with `@pytest.mark.parametrize`, one row per time.
- Fix the argument names in `TestGetSunriseSunset` and give `test_get_sunrise_sunset__call`
  a real assertion.
- Make `test_get_sunrise_sunset_times_http_error` able to fail. Break the code on purpose
  first and check the test goes red.
- Write a test for `check()` in `src/night_shift/__init__.py`, which is still uncovered
  (the coverage report lists it as lines 10-11).
