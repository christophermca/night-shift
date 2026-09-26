# pytest ↔ Jest ↔ JUnit 5 / Mockito

Use when teaching someone who knows JS or Java testing.

| Concept | pytest / unittest.mock | Jest | JUnit 5 + Mockito |
|---|---|---|---|
| Test discovery | `test_*.py`, `def test_*` | `*.test.js`, `test()` | `@Test` |
| Grouping | `class Test*` (no `__init__`) | `describe()` | test class / `@Nested` |
| Assert | `assert x == y` | `expect(x).toBe(y)` | `assertEquals(y, x)` |
| Identity | `assert a is b` | `toBe` on objects | `assertSame` |
| Expect exception | `with pytest.raises(E, match="re"):` | `expect(fn).toThrow()` | `assertThrows` |
| Setup/teardown | fixture with `yield` | `beforeEach`/`afterEach` | `@BeforeEach`/`@AfterEach` |
| Always-on setup | `@pytest.fixture(autouse=True)` | top-level `beforeEach` | base-class `@BeforeEach` |
| Shared across files | `tests/conftest.py` | `setupFilesAfterEnv` | base class / extension |
| Dependency injection | fixture name as parameter | — | constructor/extension injection |
| Fake object | `MagicMock()` | `jest.fn()` | `mock(Foo.class)` |
| Replace a dependency | `patch("mod.name")` | `jest.mock("mod")` | `@Mock` + `@InjectMocks` |
| Stub return | `m.return_value = x` | `mockReturnValue(x)` | `when(...).thenReturn(x)` |
| Stub sequence | `m.side_effect = [a, b]` | `mockReturnValueOnce` chain | `thenReturn(a, b)` |
| Stub throw | `m.side_effect = Exc()` | `mockImplementation(() => {throw})` | `thenThrow` |
| Stub with logic | `m.side_effect = fn` | `mockImplementation(fn)` | `thenAnswer` |
| Verify call | `assert_called_once_with(a)` | `toHaveBeenCalledWith(a)` | `verify(m).f(a)` |
| Capture arg | `m.call_args.args[0]` | `m.mock.calls[0][0]` | `ArgumentCaptor` |
| Call order | `m.call_args_list[0] == call(...)` | `mock.calls[0]` | `InOrder` |
| Type-safe mock | `spec=` / `create_autospec` | TS types | built in |
| Table-driven | `@pytest.mark.parametrize` | `test.each` | `@ParameterizedTest` |
| Known-broken | `xfail(strict=True)` | `test.failing` | — |
| Temp dir | `tmp_path` | manual `mkdtemp` | `@TempDir` |
| Capture stdout | `capsys` | spy on `console.log` | redirect `System.out` |
| Temp global/env change | `monkeypatch` | manual restore | `@SetEnvironmentVariable` (ext) |
| Fake clock | patch `mod.datetime` | `jest.useFakeTimers()` | inject `Clock` |

Biggest conceptual difference to call out: `patch` replaces **one name in one
namespace at runtime** (patch where it's looked up), whereas `jest.mock` swaps
the whole module before import. And Python mocks are untyped — without `spec`
they accept anything, which Java's compiler would have rejected.
