"""Record real DSPy RLM traces for the explorer.

Usage:
    # Set API keys first (or have them in ~/.Renviron / env vars)
    export OPENAI_API_KEY="sk-..."

    # Record all demo traces
    uv run python scripts/record_traces.py

    # Record a single trace
    uv run python scripts/record_traces.py --run dspy-rlm-run-1

Requires:
    - DSPy >= 2.6 (uv pip install dspy)
    - API key for the chosen provider
    - Deno installed (for DSPy's PythonInterpreter sandbox)
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any


def load_env_from_renviron() -> None:
    """Load API keys from ~/.Renviron if they're not already in env."""
    renviron = Path.home() / ".Renviron"
    if not renviron.exists():
        return
    for line in renviron.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value


def fix_deno_env() -> None:
    """Prevent Deno from using the project's package.json for npm resolution.

    DSPy's PythonInterpreter uses Deno with `npm:pyodide`. If there's a
    package.json in the CWD or a parent, Deno 2.x tries to resolve npm
    packages from node_modules instead of its own cache, which fails.
    """
    os.environ["DENO_NO_PACKAGE_JSON"] = "1"


def record_rlm_trace(
    lm_name: str,
    question: str,
    output_path: Path,
    signature: str = "context, question -> answer",
    verbose: bool = True,
    **input_kwargs: Any,
) -> dict[str, Any]:
    """Record a single RLM trace and save to JSON.

    Args:
        lm_name: litellm-style model string (e.g., "openai/gpt-4o-mini")
        question: The question for the RLM to answer
        output_path: Where to save the JSON trace
        signature: DSPy signature string
        verbose: Whether to print progress
        **input_kwargs: Additional input kwargs for the RLM (e.g., context=...)

    Returns:
        The trace dict that was saved
    """
    import dspy
    from dspy.primitives.repl_types import REPLVariable

    lm = dspy.LM(lm_name)
    dspy.configure(lm=lm)

    rlm = dspy.RLM(
        signature=signature,
        max_iterations=15,
        verbose=verbose,
    )

    # Build inputs
    inputs: dict[str, Any] = {"question": question, **input_kwargs}

    if verbose:
        print(f"Running RLM with {lm_name}...")
        print(f"  Question: {question[:100]}...")
        print(f"  Inputs: {list(inputs.keys())}")

    start_time = time.time()
    result = rlm(**inputs)
    elapsed = time.time() - start_time

    # Extract trajectory
    trajectory: list[dict[str, str]] = getattr(result, "trajectory", [])

    # Build context_variables from the REPLVariable objects that RLM creates
    # internally. We reconstruct them from input kwargs since the variables
    # aren't directly exposed after execution.
    context_variables = []
    for name, value in inputs.items():
        value_str = str(value)
        context_variables.append({
            "name": name,
            "size_chars": len(value_str),
            "n_files": value_str.count("\n") + 1 if len(value_str) > 500 else 1,
        })

    # Detect which iteration has the SUBMIT call
    def has_submit(code: str) -> bool:
        return "SUBMIT(" in code

    # Build iterations
    iterations = []
    for i, step in enumerate(trajectory):
        code = step.get("code", "")
        output = step.get("output", "")
        is_final = has_submit(code) or i == len(trajectory) - 1
        # Check if the output indicates an error
        success = not any(
            marker in output
            for marker in ["Traceback (most recent call last)", "Error:", "Exception:"]
        )
        iterations.append({
            "iteration": i + 1,
            "reasoning": step.get("reasoning", ""),
            "code": code,
            "output": output,
            "success": success,
            "is_final": is_final,
        })

    # Try to get token usage from DSPy's LM history
    total_tokens = None
    try:
        history = lm.history
        if history:
            total_input = sum(
                entry.get("usage", {}).get("prompt_tokens", 0)
                for entry in history
            )
            total_output = sum(
                entry.get("usage", {}).get("completion_tokens", 0)
                for entry in history
            )
            if total_input > 0 or total_output > 0:
                total_tokens = {"input": total_input, "output": total_output}
    except Exception:
        pass

    # Count llm_query calls in the code
    llm_calls = sum(
        step.get("code", "").count("llm_query(")
        + step.get("code", "").count("llm_query_batched(")
        for step in trajectory
    )

    trace = {
        "run_id": output_path.stem,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": question,
        "model": lm_name,
        "context_variables": context_variables,
        "iterations": iterations,
        "final_answer": getattr(result, "answer", str(result)),
        "iterations_used": len(trajectory),
        "llm_calls_used": len(trajectory) + llm_calls,
    }
    if total_tokens:
        trace["total_tokens"] = total_tokens

    output_path.write_text(json.dumps(trace, indent=2))
    if verbose:
        print(f"Recorded: {output_path}")
        print(f"  Iterations: {len(trajectory)}")
        print(f"  Time: {elapsed:.1f}s")
        if total_tokens:
            print(
                f"  Tokens: {total_tokens['input']} in / {total_tokens['output']} out"
            )

    return trace


# Sample context: Python standard library documentation excerpts
# This gives the RLM something large enough to explore programmatically
PYTHON_COLLECTIONS_CONTEXT = """
=== collections module documentation ===

class Counter(dict):
    '''Dict subclass for counting hashable items.  Sometimes called a bag
    or multiset.  Elements are stored as dictionary keys and their counts
    are stored as dictionary values.

    >>> c = Counter('abcdeabcdabcaba')  # count elements from a string
    >>> c.most_common(3)                # three most common elements
    [('a', 5), ('b', 4), ('c', 3)]
    >>> sorted(c)                       # list all unique elements
    ['a', 'b', 'c', 'd', 'e']
    >>> ''.join(sorted(c.elements()))   # list elements with repetitions
    'aaaaabbbbcccdde'
    '''

    def __init__(self, iterable=None, /, **kwds):
        super().__init__()
        self.update(iterable, **kwds)

    def most_common(self, n=None):
        '''List the n most common elements and their counts from the most
        common to the least.  If n is None, then list all element counts.
        '''
        if n is None:
            return sorted(self.items(), key=_itemgetter(1), reverse=True)
        return _heapq.nlargest(n, self.items(), key=_itemgetter(1))

    def elements(self):
        '''Iterator over elements repeating each as many times as its count.
        If an element's count is less than one, elements() will ignore it.
        '''
        return _chain.from_iterable(_starmap(_repeat, self.items()))

    def update(self, iterable=None, /, **kwds):
        '''Like dict.update() but add counts instead of replacing them.'''
        if iterable is not None:
            if isinstance(iterable, _count_elements):
                if self:
                    self_get = self.get
                    for elem, count in iterable.items():
                        self[elem] = count + self_get(elem, 0)
                else:
                    super().update(iterable)
            else:
                _count_elements(self, iterable)
        if kwds:
            self.update(kwds)

    def subtract(self, iterable=None, /, **kwds):
        '''Like dict.update() but subtracts counts instead of replacing them.'''
        if iterable is not None:
            if isinstance(iterable, Mapping):
                for elem, count in iterable.items():
                    self[elem] = self[elem] - count
            else:
                for elem in iterable:
                    self[elem] -= 1
        if kwds:
            self.subtract(kwds)

    def total(self):
        '''Sum of all counts.'''
        return sum(self.values())

class defaultdict(dict):
    '''dict subclass that calls a factory function to supply missing values.

    >>> s = [('yellow', 1), ('blue', 2), ('yellow', 3), ('blue', 4), ('red', 1)]
    >>> d = defaultdict(list)
    >>> for k, v in s:
    ...     d[k].append(v)
    ...
    >>> sorted(d.items())
    [('blue', [2, 4]), ('red', [1]), ('yellow', [1, 3])]
    '''

    def __init__(self, default_factory=None, /, *args, **kwds):
        super().__init__(*args, **kwds)
        self.default_factory = default_factory

    def __missing__(self, key):
        if self.default_factory is None:
            raise KeyError(key)
        self[key] = value = self.default_factory()
        return value

class OrderedDict(dict):
    '''Dictionary that remembers insertion order.

    In Python 3.7+, regular dicts maintain insertion order, so OrderedDict
    is mainly useful for:
    - move_to_end() method
    - Equality comparison that considers order
    - __reversed__() support (also in regular dict since 3.8)
    '''

    def move_to_end(self, key, last=True):
        '''Move an existing element to either end of an ordered dictionary.
        The item is moved to the right end if last is true (the default)
        or to the beginning if last is false.
        '''
        ...

class deque:
    '''Double-ended queue implemented as a doubly-linked list of fixed-length blocks.

    >>> from collections import deque
    >>> d = deque('ghi')
    >>> d.append('j')
    >>> d.appendleft('f')
    >>> d
    deque(['f', 'g', 'h', 'i', 'j'])

    Bounded length deques provide functionality similar to the tail filter in Unix:
    >>> d = deque(maxlen=3)
    >>> d.extend([1, 2, 3, 4, 5])
    >>> d
    deque([3, 4, 5], maxlen=3)

    Supports thread-safe, memory efficient appends and pops from either side
    with approximately the same O(1) performance in either direction.
    '''

    def append(self, x): ...
    def appendleft(self, x): ...
    def pop(self): ...
    def popleft(self): ...
    def extend(self, iterable): ...
    def extendleft(self, iterable): ...
    def rotate(self, n=1): ...
    def clear(self): ...
    def count(self, x): ...
    def index(self, x, start=0, stop=None): ...
    def insert(self, i, x): ...
    def remove(self, value): ...
    def reverse(self): ...
    def copy(self): ...
    @property
    def maxlen(self): ...

class namedtuple:
    '''Factory function for creating tuple subclasses with named fields.

    >>> Point = namedtuple('Point', ['x', 'y'])
    >>> p = Point(11, y=22)
    >>> p[0] + p[1]
    33
    >>> p.x + p.y
    33
    >>> p._replace(x=100)
    Point(x=100, y=22)
    >>> p._asdict()
    {'x': 11, 'y': 22}
    '''

class ChainMap(MutableMapping):
    '''A ChainMap groups multiple dicts (or other mappings) together
    to create a single, updateable view.

    >>> baseline = {'music': 'bach', 'art': 'rembrandt'}
    >>> adjustments = {'art': 'van gogh', 'opera': 'carmen'}
    >>> ChainMap(adjustments, baseline)
    ChainMap({'art': 'van gogh', 'opera': 'carmen'}, {'music': 'bach', 'art': 'rembrandt'})

    The underlying mappings are stored in a list accessible via the maps attribute.
    Lookups search the underlying mappings successively until a key is found.
    '''

    def __init__(self, *maps):
        self.maps = list(maps) or [{}]

    def new_child(self, m=None, **kwargs):
        '''New ChainMap with a new map followed by all previous maps.'''
        ...

    @property
    def parents(self):
        '''New ChainMap from maps[1:].'''
        return self.__class__(*self.maps[1:])
"""

FLASK_APP_CONTEXT = """
=== Flask application source code ===

# --- app.py ---
import typing as t
from .scaffold import Scaffold
from .globals import request_ctx
from .wrappers import Request, Response

class Flask(Scaffold):
    '''The Flask application class. An instance of this is the WSGI application.

    Implements the WSGI interface via __call__.

    Parameters:
      import_name: The name of the application package.
      static_url_path: Override the default static URL path.
      static_folder: Folder with static files (default 'static').
      template_folder: Folder for Jinja templates (default 'templates').
    '''

    request_class: type[Request] = Request
    response_class: type[Response] = Response

    testing: bool = False
    secret_key: str | bytes | None = None

    default_config: dict = {
        "DEBUG": False,
        "TESTING": False,
        "SECRET_KEY": None,
        "PERMANENT_SESSION_LIFETIME": 2678400,  # 31 days
        "MAX_CONTENT_LENGTH": None,
        "PREFERRED_URL_SCHEME": "http",
    }

    # URL rule storage
    url_map: Map  # werkzeug.routing.Map
    url_rule_class: type[Rule] = Rule

    # Request lifecycle hooks
    before_request_funcs: dict[str | None, list[t.Callable]] = {}
    after_request_funcs: dict[str | None, list[t.Callable]] = {}
    teardown_request_funcs: dict[str | None, list[t.Callable]] = {}
    error_handler_spec: dict[str | None, dict[int, list[t.Callable]]] = {}

    def __init__(self, import_name: str, **kwargs):
        super().__init__(import_name, **kwargs)
        self.config = self.make_config()
        self.url_map = Map()
        self.view_functions: dict[str, t.Callable] = {}
        self.before_request_funcs = {}
        self.after_request_funcs = {}

    # --- Decorator: @app.route ---
    def route(self, rule: str, **options: t.Any) -> t.Callable:
        '''Register a URL rule via a decorator.

        @app.route("/")
        def index():
            return "Hello!"

        This is a convenience wrapper around add_url_rule().
        '''
        def decorator(f: t.Callable) -> t.Callable:
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule: str, endpoint: str | None = None,
                     view_func: t.Callable | None = None, **options):
        '''Register a URL rule. Called by route() decorator.

        Creates a werkzeug.routing.Rule and adds it to url_map.
        Also stores the view function in view_functions dict.
        '''
        if endpoint is None:
            endpoint = view_func.__name__
        methods = options.pop("methods", ("GET",))
        rule_obj = self.url_rule_class(rule, methods=methods, endpoint=endpoint)
        self.url_map.add(rule_obj)
        self.view_functions[endpoint] = view_func

    # --- Decorator: @app.before_request ---
    def before_request(self, f: t.Callable) -> t.Callable:
        '''Register a function to run before each request.'''
        self.before_request_funcs.setdefault(None, []).append(f)
        return f

    # --- Decorator: @app.after_request ---
    def after_request(self, f: t.Callable) -> t.Callable:
        '''Register a function to run after each request.
        Must accept and return a Response object.'''
        self.after_request_funcs.setdefault(None, []).append(f)
        return f

    # --- Decorator: @app.errorhandler ---
    def errorhandler(self, code_or_exception: type[Exception] | int):
        '''Register a function for handling errors by code or exception.

        @app.errorhandler(404)
        def not_found(e):
            return "Not Found", 404
        '''
        def decorator(f: t.Callable) -> t.Callable:
            self.register_error_handler(code_or_exception, f)
            return f
        return decorator

    # --- Request dispatching ---
    def full_dispatch_request(self) -> Response:
        '''Dispatch the request plus perform request pre/post processing.

        1. Run before_request hooks (may short-circuit)
        2. Dispatch to view function
        3. Run after_request hooks on the response
        4. Return final response
        '''
        try:
            rv = self.try_trigger_before_first_request_functions()
            if rv is None:
                rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
        except Exception as e:
            rv = self.handle_exception(e)
        response = self.make_response(rv)
        response = self.process_response(response)
        return response

    def preprocess_request(self) -> Response | None:
        '''Run before_request hooks. If any returns a value, skip dispatch.'''
        for func in self.before_request_funcs.get(None, []):
            rv = func()
            if rv is not None:
                return rv
        return None

    def dispatch_request(self) -> Response:
        '''Match the URL, call the view function.'''
        rule = request_ctx.url_adapter.match()
        return self.view_functions[rule.endpoint](**rule.arguments)

    def process_response(self, response: Response) -> Response:
        '''Run after_request hooks on the response.'''
        for func in reversed(self.after_request_funcs.get(None, [])):
            response = func(response)
        return response

    # --- WSGI interface ---
    def __call__(self, environ, start_response):
        '''WSGI application interface.'''
        return self.wsgi_app(environ, start_response)

    def wsgi_app(self, environ, start_response):
        '''The actual WSGI app. Pushes a request context and dispatches.'''
        ctx = self.request_context(environ)
        ctx.push()
        try:
            response = self.full_dispatch_request()
            return response(environ, start_response)
        finally:
            ctx.pop()

# --- scaffold.py ---
class Scaffold:
    '''Base class shared by Flask and Blueprint.

    Provides the route(), before_request(), etc. decorator interface.
    '''
    name: str
    import_name: str
    static_folder: str | None
    template_folder: str | None

# --- blueprints.py ---
class Blueprint(Scaffold):
    '''Represents a collection of views and other code that can be
    registered on the application later.

    Blueprints allow modular application structure:

    auth = Blueprint('auth', __name__, url_prefix='/auth')

    @auth.route('/login')
    def login():
        return render_template('login.html')
    '''
    def __init__(self, name: str, import_name: str, url_prefix: str | None = None):
        super().__init__(import_name)
        self.name = name
        self.url_prefix = url_prefix
        self.deferred_functions: list[t.Callable] = []

    def register(self, app: Flask, options: dict):
        '''Called by app.register_blueprint(). Applies deferred functions.'''
        for deferred in self.deferred_functions:
            deferred(app)

    def route(self, rule: str, **options):
        '''Blueprint-level route decorator. Defers registration until
        the blueprint is registered with an app.'''
        def decorator(f):
            self.deferred_functions.append(
                lambda app: app.add_url_rule(
                    self.url_prefix + rule, f.__name__, f, **options
                )
            )
            return f
        return decorator

# --- globals.py ---
from werkzeug.local import LocalStack, LocalProxy

_request_ctx_stack = LocalStack()
request_ctx = _request_ctx_stack()
request = LocalProxy(lambda: request_ctx.request)
g = LocalProxy(lambda: request_ctx.g)
session = LocalProxy(lambda: request_ctx.session)
"""


DEMOS: list[dict[str, Any]] = [
    {
        "name": "dspy-rlm-run-1",
        "lm": "openai/gpt-4o-mini",
        "signature": "context, question -> answer",
        "question": (
            "What are the three main decorator patterns in Flask "
            "and how does the request lifecycle work?"
        ),
        "kwargs": {"context": FLASK_APP_CONTEXT},
    },
    {
        "name": "dspy-rlm-run-2",
        "lm": "openai/gpt-4o-mini",
        "signature": "context, question -> answer",
        "question": (
            "Compare Counter, defaultdict, and deque from the collections module. "
            "When would you use each one, and what are their key differences?"
        ),
        "kwargs": {"context": PYTHON_COLLECTIONS_CONTEXT},
    },
    {
        "name": "dspy-rlm-run-3",
        "lm": "openai/gpt-4o",
        "signature": "context, question -> answer",
        "question": (
            "Trace through the Flask request lifecycle from WSGI call "
            "to final response. What hooks can modify the request/response?"
        ),
        "kwargs": {"context": FLASK_APP_CONTEXT},
    },
]


def main() -> None:
    """Record demo traces."""
    load_env_from_renviron()
    fix_deno_env()

    output_dir = Path("src/dspy_explorer/data/runs")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Allow recording a single run by name
    target = None
    if len(sys.argv) > 1:
        if sys.argv[1] == "--run" and len(sys.argv) > 2:
            target = sys.argv[2]
        elif sys.argv[1] == "--help":
            print(__doc__)
            sys.exit(0)
        else:
            target = sys.argv[1]

    demos_to_run = DEMOS
    if target:
        demos_to_run = [d for d in DEMOS if d["name"] == target]
        if not demos_to_run:
            print(f"Unknown run: {target}")
            print(f"Available: {', '.join(d['name'] for d in DEMOS)}")
            sys.exit(1)

    for demo in demos_to_run:
        print(f"\n{'=' * 60}")
        print(f"Recording: {demo['name']}")
        print(f"{'=' * 60}\n")
        try:
            record_rlm_trace(
                lm_name=demo["lm"],
                question=demo["question"],
                output_path=output_dir / f"{demo['name']}.json",
                signature=demo.get("signature", "context, question -> answer"),
                **demo.get("kwargs", {}),
            )
        except Exception as e:
            print(f"FAILED: {demo['name']}: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
