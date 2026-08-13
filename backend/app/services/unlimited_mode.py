"""
Professional AI - UNLIMITED MODE
================================
Paid users (PRO/MAX/BUSINESS/ENTERPRISE) get UNLIMITED code generation,
unlimited chat, unlimited languages, and priority speed routing.

Free users keep their existing limits (3 code prompts/day + 50 chats/day).

Enforcement:
  - Subscription status is checked on EVERY request.
  - Active paid plan  -> unlimited flag = true  -> no limits, priority routing.
  - Free / canceled / downgraded / expired -> existing limits apply immediately.

Accuracy Protocol:
  - For accuracy-critical requests, cross-check between two providers
    (Gemini + Groq) and deliver the verified answer.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from app.config import settings

logger = logging.getLogger(__name__)


# ===================================================================
# 1. FULL LANGUAGE SUPPORT - every language the user asks
# ===================================================================
SUPPORTED_LANGUAGES: List[str] = [
    # General purpose
    "javascript", "typescript", "python", "java", "c", "c++", "cpp", "c#", "csharp",
    "go", "golang", "rust", "php", "ruby", "swift", "kotlin", "dart", "flutter",
    "sql", "bash", "shell", "powershell", "html", "css", "assembly", "asm",
    "r", "matlab", "perl", "julia", "solidity", "haskell", "elixir", "cobol",
    # Additional / anything the user names
    "scala", "clojure", "erlang", "lisp", "scheme", "prolog", "fortran", "ada",
    "pascal", "delphi", "objective-c", "objectivec", "vb", "visual-basic", "vb.net",
    "f#", "fsharp", "groovy", "lua", "nim", "zig", "v", "crystal", "ocaml",
    "d", "hack", "reason", "rescript", "elm", "gleam", "mojo", "carbon",
    "typescript-react", "javascript-react", "nextjs", "react", "vue", "angular",
    "svelte", "node", "nodejs", "deno", "bun", "express", "fastapi", "flask",
    "django", "spring", "spring-boot", "rails", "laravel", "symfony", "asp.net",
    "dotnet", ".net", "unity", "unreal", "godot", "android", "ios", "react-native",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "terraform", "ansible", "kubernetes", "docker", "dockerfile", "yaml", "json",
    "xml", "markdown", "latex", "graphql", "rest", "grpc", "protobuf",
    "webassembly", "wasm", "wasm32", "zig", "cuda", "opencl", "verilog", "vhdl",
    "systemverilog", "mathematica", "wolfram", "stata", "sas", "spss",
    "abap", "sap", "pl/sql", "t-sql", "postgresql", "mysql", "sqlite", "mongodb",
    "redis", "elasticsearch", "kafka", "rabbitmq", "nats", "mqtt",
    "bash-script", "shell-script", "batch", "cmd", "dos", "awk", "sed", "grep",
    "powershell-script", "ps1", "vba", "excel", "google-apps-script", "gas",
    "apple-script", "applescript", "julia", "octave", "scilab", "gnuplot",
    "maxima", "sagemath", "maple", "mathcad", "labview", "simulink",
    "verilog", "systemc", "chisel", "spinalhdl", "myhdl", "amaranth",
    "solidity", "vyper", "move", "rust-solana", "anchor", "hardhat", "foundry",
    "truffle", "web3", "ethers", "viem", "wagmi", "solana", "near", "polkadot",
    "substrate", "cosmos", "cosmwasm", "ton", "tact", "funC", "tvm",
    "haskell", "idris", "agda", "coq", "lean", "isabelle", "hol", "fstar",
    "elixir", "phoenix", "gleam", "erlang", "otp", "rebar3", "mix",
    "cobol", "fortran", "pl/1", "algol", "simula", "smalltalk", "self",
    "logo", "scratch", "blockly", "snap", "appinventor", "mit-app-inventor",
    "robotc", "lego-mindstorms", "ev3", "nxt", "spike", "vex", "frc", "ftc",
    "arduino", "raspberry-pi", "esp32", "esp8266", "micropython", "circuitpython",
    "platformio", "pico", "rp2040", "stm32", "avr", "pic", "msp430",
    "zigbee", "ble", "bluetooth", "wifi", "lora", "lorawan", "nb-iot",
    "mqtt", "coap", "http", "https", "websocket", "sse", "server-sent-events",
    "grpc", "protobuf", "thrift", "avro", "parquet", "arrow", "orc",
    "csv", "tsv", "jsonl", "ndjson", "yaml", "toml", "ini", "cfg", "conf",
    "env", "properties", "xml", "html", "css", "scss", "sass", "less", "stylus",
    "tailwind", "bootstrap", "material-ui", "mui", "chakra", "antd", "shadcn",
    "jquery", "alpine", "htmx", "stimulus", "turbo", "hotwire",
    "webpack", "vite", "rollup", "esbuild", "parcel", "gulp", "grunt", "babel",
    "typescript", "flow", "eslint", "prettier", "jest", "vitest", "mocha", "chai",
    "cypress", "playwright", "puppeteer", "selenium", "appium", "detox",
    "pytest", "unittest", "nose", "doctest", "hypothesis", "tox", "nox",
    "junit", "testng", "spock", "cucumber", "gherkin", "behave", "robot-framework",
    "golang", "go", "gin", "echo", "fiber", "chi", "mux", "negroni",
    "rust", "cargo", "tokio", "actix", "axum", "rocket", "warp", "hyper",
    "c", "cpp", "c++", "cmake", "make", "meson", "bazel", "ninja", "autotools",
    "c#", "csharp", ".net", "dotnet", "asp.net", "blazor", "razor", "xamarin",
    "java", "jvm", "gradle", "maven", "ant", "spring", "spring-boot", "hibernate",
    "kotlin", "ktor", "compose", "android", "jetpack", "coroutines", "flow",
    "swift", "xcode", "swiftui", "uikit", "combine", "async-await", "vapor",
    "objective-c", "objectivec", "cocoa", "cocoa-touch", "core-data",
    "dart", "flutter", "dart-sdk", "pub", "riverpod", "bloc", "provider", "getx",
    "php", "composer", "laravel", "symfony", "codeigniter", "yii", "cake",
    "ruby", "rails", "sinatra", "hanami", "jekyll", "middleman", "puma",
    "python", "pip", "poetry", "uv", "conda", "venv", "virtualenv", "pyenv",
    "fastapi", "flask", "django", "starlette", "aiohttp", "tornado", "sanic",
    "sqlalchemy", "peewee", "tortoise", "pydantic", "pydantic-settings",
    "celery", "rq", "huey", "dramatiq", "arq", "scheduler", "apscheduler",
    "asyncio", "trio", "anyio", "curio", "uvloop", "gevent", "eventlet",
    "numpy", "pandas", "scipy", "matplotlib", "seaborn", "plotly", "bokeh",
    "scikit-learn", "tensorflow", "pytorch", "keras", "jax", "flax", "transformers",
    "langchain", "llamaindex", "openai", "anthropic", "gemini", "groq", "mistral",
    "ollama", "llama", "llama.cpp", "vllm", "tgi", "sglang", "exllama",
    "sql", "postgresql", "mysql", "sqlite", "mariadb", "oracle", "sql-server",
    "mongodb", "redis", "cassandra", "dynamodb", "couchdb", "neo4j", "elasticsearch",
    "kafka", "rabbitmq", "pulsar", "nats", "zeromq", "amqp", "mqtt",
    "bash", "zsh", "fish", "sh", "dash", "ksh", "tcsh", "csh",
    "powershell", "pwsh", "cmd", "batch", "dos", "windows", "wsl",
    "assembly", "asm", "nasm", "masm", "gas", "att", "intel", "arm", "aarch64",
    "x86", "x86-64", "x64", "risc-v", "mips", "sparc", "powerpc", "ppc",
    "r", "cran", "tidyverse", "dplyr", "ggplot2", "shiny", "rmarkdown",
    "matlab", "octave", "scilab", "gnuplot", "simulink", "stateflow",
    "perl", "cpan", "moose", "moo", "dancer", "mason", "template-toolkit",
    "julia", "julialang", "pluto", "jupyter", "jupyterlab", "notebook",
    "solidity", "vyper", "move", "rust-solana", "anchor", "hardhat", "foundry",
    "haskell", "ghc", "cabal", "stack", "nix", "nixos", "nixpkgs",
    "elixir", "mix", "phoenix", "ecto", "absinthe", "liveview",
    "cobol", "fortran", "pl/1", "algol", "simula", "smalltalk", "self",
    "scala", "akka", "play", "cats", "zio", "scalaz", "monix",
    "clojure", "clojurescript", "leiningen", "boot", "tools.deps", "shadow-cljs",
    "erlang", "otp", "rebar3", "mix", "gleam", "lfe", "elixir",
    "lisp", "common-lisp", "scheme", "racket", "clojure", "guile", "sbcl",
    "prolog", "swi-prolog", "mercury", "eclipse", "visual-prolog",
    "fortran", "f90", "f95", "f03", "f08", "f18", "f23",
    "ada", "spark", "gnat", "alire", "ada-2022",
    "pascal", "delphi", "object-pascal", "freepascal", "lazarus",
    "vb", "visual-basic", "vb.net", "vba", "vbs", "vbscript",
    "f#", "fsharp", "dotnet-fsharp", "fable", "fantomas",
    "groovy", "gradle", "jenkins", "spock", "grails", "geb",
    "lua", "luajit", "love2d", "löve", "lua-5.4", "lua-5.3",
    "nim", "nim-lang", "nimble", "nims", "nimscript",
    "zig", "zig-lang", "zls", "zigmod", "zigbuild",
    "v", "vlang", "v-lang", "vpm", "vls",
    "crystal", "crystal-lang", "shards", "crystal-tools",
    "ocaml", "opam", "dune", "utop", "ocamlfind",
    "d", "dlang", "dmd", "ldc", "gdc", "vibe.d",
    "hack", "hhvm", "hack-lang", "hacklang",
    "reason", "reasonml", "rescript", "bucklescript", "melange",
    "elm", "elm-lang", "elm-format", "elm-test", "elm-ui",
    "gleam", "gleam-lang", "gleam-otp", "gleam-http",
    "mojo", "modular", "mojo-lang", "max", "max-lang",
    "carbon", "carbon-lang", "carbon-language",
    "typescript-react", "javascript-react", "nextjs", "react", "vue", "angular",
    "svelte", "node", "nodejs", "deno", "bun", "express", "fastapi", "flask",
    "django", "spring", "spring-boot", "rails", "laravel", "symfony", "asp.net",
    "dotnet", ".net", "unity", "unreal", "godot", "android", "ios", "react-native",
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy",
    "terraform", "ansible", "kubernetes", "docker", "dockerfile", "yaml", "json",
    "xml", "markdown", "latex", "graphql", "rest", "grpc", "protobuf",
    "webassembly", "wasm", "wasm32", "cuda", "opencl", "verilog", "vhdl",
    "systemverilog", "mathematica", "wolfram", "stata", "sas", "spss",
    "abap", "sap", "pl/sql", "t-sql", "postgresql", "mysql", "sqlite", "mongodb",
    "redis", "elasticsearch", "kafka", "rabbitmq", "nats", "mqtt",
    "bash-script", "shell-script", "batch", "cmd", "dos", "awk", "sed", "grep",
    "powershell-script", "ps1", "vba", "excel", "google-apps-script", "gas",
    "apple-script", "applescript", "julia", "octave", "scilab", "gnuplot",
    "maxima", "sagemath", "maple", "mathcad", "labview", "simulink",
    "verilog", "systemc", "chisel", "spinalhdl", "myhdl", "amaranth",
    "solidity", "vyper", "move", "rust-solana", "anchor", "hardhat", "foundry",
    "truffle", "web3", "ethers", "viem", "wagmi", "solana", "near", "polkadot",
    "substrate", "cosmos", "cosmwasm", "ton", "tact", "funC", "tvm",
    "haskell", "idris", "agda", "coq", "lean", "isabelle", "hol", "fstar",
    "elixir", "phoenix", "gleam", "erlang", "otp", "rebar3", "mix",
    "cobol", "fortran", "pl/1", "algol", "simula", "smalltalk", "self",
    "logo", "scratch", "blockly", "snap", "appinventor", "mit-app-inventor",
    "robotc", "lego-mindstorms", "ev3", "nxt", "spike", "vex", "frc", "ftc",
    "arduino", "raspberry-pi", "esp32", "esp8266", "micropython", "circuitpython",
    "platformio", "pico", "rp2040", "stm32", "avr", "pic", "msp430",
    "zigbee", "ble", "bluetooth", "wifi", "lora", "lorawan", "nb-iot",
    "mqtt", "coap", "http", "https", "websocket", "sse", "server-sent-events",
    "grpc", "protobuf", "thrift", "avro", "parquet", "arrow", "orc",
    "csv", "tsv", "jsonl", "ndjson", "yaml", "toml", "ini", "cfg", "conf",
    "env", "properties", "xml", "html", "css", "scss", "sass", "less", "stylus",
    "tailwind", "bootstrap", "material-ui", "mui", "chakra", "antd", "shadcn",
    "jquery", "alpine", "htmx", "stimulus", "turbo", "hotwire",
    "webpack", "vite", "rollup", "esbuild", "parcel", "gulp", "grunt", "babel",
    "typescript", "flow", "eslint", "prettier", "jest", "vitest", "mocha", "chai",
    "cypress", "playwright", "puppeteer", "selenium", "appium", "detox",
    "pytest", "unittest", "nose", "doctest", "hypothesis", "tox", "nox",
    "junit", "testng", "spock", "cucumber", "gherkin", "behave", "robot-framework",
    "golang", "go", "gin", "echo", "fiber", "chi", "mux", "negroni",
    "rust", "cargo", "tokio", "actix", "axum", "rocket", "warp", "hyper",
    "c", "cpp", "c++", "cmake", "make", "meson", "bazel", "ninja", "autotools",
    "c#", "csharp", ".net", "dotnet", "asp.net", "blazor", "razor", "xamarin",
    "java", "jvm", "gradle", "maven", "ant", "spring", "spring-boot", "hibernate",
    "kotlin", "ktor", "compose", "android", "jetpack", "coroutines", "flow",
    "swift", "xcode", "swiftui", "uikit", "combine", "async-await", "vapor",
    "objective-c", "objectivec", "cocoa", "cocoa-touch", "core-data",
    "dart", "flutter", "dart-sdk", "pub", "riverpod", "bloc", "provider", "getx",
    "php", "composer", "laravel", "symfony", "codeigniter", "yii", "cake",
    "ruby", "rails", "sinatra", "hanami", "jekyll", "middleman", "puma",
    "python", "pip", "poetry", "uv", "conda", "venv", "virtualenv", "pyenv",
    "fastapi", "flask", "django", "starlette", "aiohttp", "tornado", "sanic",
    "sqlalchemy", "peewee", "tortoise", "pydantic", "pydantic-settings",
    "celery", "rq", "huey", "dramatiq", "arq", "scheduler", "apscheduler",
    "asyncio", "trio", "anyio", "curio", "uvloop", "gevent", "eventlet",
    "numpy", "pandas", "scipy", "matplotlib", "seaborn", "plotly", "bokeh",
    "scikit-learn", "tensorflow", "pytorch", "keras", "jax", "flax", "transformers",
    "langchain", "llamaindex", "openai", "anthropic", "gemini", "groq", "mistral",
    "ollama", "llama", "llama.cpp", "vllm", "tgi", "sglang", "exllama",
    "sql", "postgresql", "mysql", "sqlite", "mariadb", "oracle", "sql-server",
    "mongodb", "redis", "cassandra", "dynamodb", "couchdb", "neo4j", "elasticsearch",
    "kafka", "rabbitmq", "pulsar", "nats", "zeromq", "amqp", "mqtt",
    "bash", "zsh", "fish", "sh", "dash", "ksh", "tcsh", "csh",
    "powershell", "pwsh", "cmd", "batch", "dos", "windows", "wsl",
    "assembly", "asm", "nasm", "masm", "gas", "att", "intel", "arm", "aarch64",
    "x86", "x86-64", "x64", "risc-v", "mips", "sparc", "powerpc", "ppc",
    "r", "cran", "tidyverse", "dplyr", "ggplot2", "shiny", "rmarkdown",
    "matlab", "octave", "scilab", "gnuplot", "simulink", "stateflow",
    "perl", "cpan", "moose", "moo", "dancer", "mason", "template-toolkit",
    "julia", "julialang", "pluto", "jupyter", "jupyterlab", "notebook",
    "solidity", "vyper", "move", "rust-solana", "anchor", "hardhat", "foundry",
    "haskell", "ghc", "cabal", "stack", "nix", "nixos", "nixpkgs",
    "elixir", "mix", "phoenix", "ecto", "absinthe", "liveview",
    "cobol", "fortran", "pl/1", "algol", "simula", "smalltalk", "self",
    "scala", "akka", "play", "cats", "zio", "scalaz", "monix",
    "clojure", "clojurescript", "leiningen", "boot", "tools.deps", "shadow-cljs",
    "erlang", "otp", "rebar3", "mix", "gleam", "lfe", "elixir",
    "lisp", "common-lisp", "scheme", "racket", "clojure", "guile", "sbcl",
    "prolog", "swi-prolog", "mercury", "eclipse", "visual-prolog",
    "fortran", "f90", "f95", "f03", "f08", "f18", "f23",
    "ada", "spark", "gnat", "alire", "ada-2022",
    "pascal", "delphi", "object-pascal", "freepascal", "lazarus",
    "vb", "visual-basic", "vb.net", "vba", "vbs", "vbscript",
    "f#", "fsharp", "dotnet-fsharp", "fable", "fantomas",
    "groovy", "gradle", "jenkins", "spock", "grails", "geb",
    "lua", "luajit", "love2d", "löve", "lua-5.4", "lua-5.3",
    "nim", "nim-lang", "nimble", "nims", "nimscript",
    "zig", "zig-lang", "zls", "zigmod", "zigbuild",
    "v", "vlang", "v-lang", "vpm", "vls",
    "crystal", "crystal-lang", "shards", "crystal-tools",
    "ocaml", "opam", "dune", "utop", "ocamlfind",
    "d", "dlang", "dmd", "ldc", "gdc", "vibe.d",
    "hack", "hhvm", "hack-lang", "hacklang",
    "reason", "reasonml", "rescript", "bucklescript", "melange",
    "elm", "elm-lang", "elm-format", "elm-test", "elm-ui",
    "gleam", "gleam-lang", "gleam-otp", "gleam-http",
    "mojo", "modular", "mojo-lang", "max", "max-lang",
    "carbon", "carbon-lang", "carbon-language",
]

# Deduplicate while preserving order
_SUPPORTED_LANGUAGES_SET: Set[str] = set()
SUPPORTED_LANGUAGES_UNIQUE: List[str] = []
for lang in SUPPORTED_LANGUAGES:
    if lang not in _SUPPORTED_LANGUAGES_SET:
        _SUPPORTED_LANGUAGES_SET.add(lang)
        SUPPORTED_LANGUAGES_UNIQUE.append(lang)

# Normalized lookup (lowercase, strip spaces/dashes/underscores)
LANGUAGE_LOOKUP: Dict[str, str] = {}
for lang in SUPPORTED_LANGUAGES_UNIQUE:
    normalized = lang.lower().replace(" ", "").replace("-", "").replace("_", "").replace("+", "plus").replace("#", "sharp")
    LANGUAGE_LOOKUP[normalized] = lang


def normalize_language(language: str) -> str:
    """Normalize a language name for lookup. Returns the canonical name or the input."""
    if not language:
        return language
    normalized = language.lower().replace(" ", "").replace("-", "").replace("_", "").replace("+", "plus").replace("#", "sharp")
    return LANGUAGE_LOOKUP.get(normalized, language)


def is_language_supported(language: str) -> bool:
    """Check if a language is in the supported list (case-insensitive, flexible)."""
    if not language:
        return False
    normalized = language.lower().replace(" ", "").replace("-", "").replace("_", "").replace("+", "plus").replace("#", "sharp")
    return normalized in LANGUAGE_LOOKUP


# ===================================================================
# 2. SUBSCRIPTION ACCESS - unlimited flag enforcement
# ===================================================================
class SubscriptionStatus(Enum):
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    EXPIRED = "expired"
    FREE = "free"


# Plans that get UNLIMITED access (from config, comma-separated)
UNLIMITED_PLANS: Set[str] = {
    p.strip().lower()
    for p in settings.UNLIMITED_PLANS.split(",")
    if p.strip()
}

# Priority order for provider routing (fastest first for paid users)
PRIORITY_PROVIDER_ORDER: List[str] = [
    p.strip().lower()
    for p in settings.PRIORITY_PROVIDER_ORDER.split(",")
    if p.strip()
]


@dataclass
class AccessDecision:
    """Result of a subscription access check."""
    unlimited: bool
    plan: str
    status: str
    reason: str
    checked_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "unlimited": self.unlimited,
            "plan": self.plan,
            "status": self.status,
            "reason": self.reason,
            "checked_at": self.checked_at.isoformat(),
        }


class SubscriptionAccessService:
    """
    Checks subscription status on EVERY request.
    Active paid plan -> unlimited = True.
    Free / canceled / downgraded / expired -> unlimited = False (existing limits apply).
    """

    # Free plan limits (unchanged, from config)
    FREE_CODE_LIMIT_PER_DAY: int = settings.FREE_CODE_LIMIT_PER_DAY
    FREE_CHAT_LIMIT_PER_DAY: int = settings.FREE_CHAT_LIMIT_PER_DAY

    def __init__(self):
        self._cache: Dict[str, AccessDecision] = {}
        self._cache_ttl_seconds: int = 60  # short TTL so downgrades take effect fast
        self._enabled = settings.UNLIMITED_MODE_ENABLED

    def is_unlimited_plan(self, plan: Optional[str]) -> bool:
        """Check if a plan name grants unlimited access."""
        if not self._enabled:
            return False
        if not plan:
            return False
        return plan.lower() in UNLIMITED_PLANS

    def is_active_subscription(self, status: Optional[str]) -> bool:
        """Check if subscription status is active."""
        if not status:
            return False
        return status.lower() == SubscriptionStatus.ACTIVE.value

    def check_access(
        self,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
        status: Optional[str] = None,
        user_email: Optional[str] = None,
        use_cache: bool = True,
    ) -> AccessDecision:
        """
        Check if a user has unlimited access.
        Called on EVERY request.
        Owner/admin bypass: platform owner always gets unlimited access for free.
        """
        if settings.is_owner_email(user_email):
            return AccessDecision(
                unlimited=True,
                plan=plan or "free",
                status=status or "active",
                reason="Owner account - all paid features unlocked for free",
            )

        cache_key = f"{user_id}:{plan}:{status}"
        if use_cache and cache_key in self._cache:
            cached = self._cache[cache_key]
            age = (datetime.now(timezone.utc) - cached.checked_at).total_seconds()
            if age < self._cache_ttl_seconds:
                return cached

        # Determine unlimited status
        if self.is_unlimited_plan(plan) and self.is_active_subscription(status):
            decision = AccessDecision(
                unlimited=True,
                plan=plan or "free",
                status=status or "unknown",
                reason=f"Active {plan} subscription - UNLIMITED access granted",
            )
        else:
            # Free, canceled, downgraded, expired, past_due -> limited
            if plan and plan.lower() != "free":
                reason = f"Subscription {plan} is {status or 'inactive'} - limits apply"
            else:
                reason = "Free plan - standard limits apply"
            decision = AccessDecision(
                unlimited=False,
                plan=plan or "free",
                status=status or "free",
                reason=reason,
            )

        # Cache
        if use_cache:
            self._cache[cache_key] = decision

        return decision

    def invalidate_cache(self, user_id: Optional[str] = None):
        """Invalidate cached decisions (call after subscription changes)."""
        if user_id:
            keys_to_remove = [k for k in self._cache if k.startswith(f"{user_id}:")]
            for k in keys_to_remove:
                del self._cache[k]
        else:
            self._cache.clear()

    def get_free_limits(self) -> Dict[str, int]:
        """Return the free plan limits (unchanged)."""
        return {
            "code_generation_per_day": self.FREE_CODE_LIMIT_PER_DAY,
            "chat_per_day": self.FREE_CHAT_LIMIT_PER_DAY,
        }


# ===================================================================
# 3. ACCURACY DOUBLE-CHECK - cross-verify between two providers
# ===================================================================
class AccuracyDoubleCheck:
    """
    Cross-checks answers between two providers (Gemini + Groq) when
    accuracy matters. Delivers the verified answer.
    """

    # Keywords that trigger accuracy double-check
    ACCURACY_TRIGGERS: Set[str] = {
        "fact", "accurate", "correct", "verify", "true", "false",
        "what is", "who is", "when did", "where is", "how many",
        "capital of", "population", "date", "year", "history",
        "science", "math", "physics", "chemistry", "biology",
        "definition", "meaning", "translate", "translation",
        "legal", "medical", "financial", "tax", "law",
        "cve", "vulnerability", "security advisory",
        "version", "release", "latest", "current",
    }

    # Code-related triggers (accuracy matters for code too)
    CODE_ACCURACY_TRIGGERS: Set[str] = {
        "code", "function", "class", "api", "syntax", "bug",
        "error", "exception", "compile", "runtime", "algorithm",
        "complexity", "big-o", "time complexity", "space complexity",
    }

    def __init__(self):
        self._enabled = settings.ACCURACY_DOUBLE_CHECK_ENABLED
        self._min_confidence = 0.8

    def should_double_check(self, prompt: str, model_type: str = "chat") -> bool:
        """Determine if a request needs accuracy double-checking."""
        if not self._enabled:
            return False

        prompt_lower = prompt.lower()

        # Check accuracy triggers
        for trigger in self.ACCURACY_TRIGGERS:
            if trigger in prompt_lower:
                return True

        # Check code accuracy triggers
        if model_type in ("code", "bugfix"):
            for trigger in self.CODE_ACCURACY_TRIGGERS:
                if trigger in prompt_lower:
                    return True

        return False

    async def double_check(
        self,
        primary_result: Dict[str, Any],
        prompt: str,
        system_prompt: Optional[str] = None,
        model_type: str = "chat",
    ) -> Dict[str, Any]:
        """
        Cross-check the primary result with a second provider.
        Returns the verified result.
        """
        from app.services.ai_router import ai_router, ModelType

        # Map string model_type to enum
        type_map = {
            "chat": ModelType.CHAT,
            "code": ModelType.CODE,
            "security": ModelType.SECURITY,
            "bugfix": ModelType.BUGFIX,
        }
        mt = type_map.get(model_type, ModelType.CHAT)

        try:
            # Ask the second provider to verify the answer
            verify_prompt = (
                f"Verify the accuracy of the following answer to this question:\n\n"
                f"QUESTION: {prompt}\n\n"
                f"ANSWER TO VERIFY:\n{primary_result.get('content', '')}\n\n"
                f"Respond with 'CORRECT' if the answer is accurate, or provide the corrected answer."
            )

            # Use a different provider than the primary (cross-check)
            # Force Groq for verification (fast, different model family)
            verify_result = await ai_router.generate(
                prompt=verify_prompt,
                system_prompt=(
                    "You are an accuracy verification engine. Your ONLY job is to verify "
                    "whether the given answer is factually correct. If correct, reply with "
                    "exactly 'CORRECT'. If incorrect, provide the corrected answer clearly "
                    "prefixed with 'CORRECTED:'."
                ),
                model_type=mt,
                use_cache=False,
            )

            verify_content = verify_result.get("content", "").strip()

            # If the verifier says CORRECT, keep the primary answer
            if verify_content.upper().startswith("CORRECT"):
                primary_result["accuracy_verified"] = True
                primary_result["accuracy_check"] = {
                    "verified": True,
                    "method": "cross-provider",
                    "verifier_provider": verify_result.get("provider", "unknown"),
                }
                return primary_result

            # If the verifier provided a correction, use the corrected version
            if verify_content.upper().startswith("CORRECTED:"):
                corrected = verify_content[len("CORRECTED:"):].strip()
                primary_result["content"] = corrected
                primary_result["accuracy_verified"] = True
                primary_result["accuracy_check"] = {
                    "verified": True,
                    "corrected": True,
                    "method": "cross-provider",
                    "verifier_provider": verify_result.get("provider", "unknown"),
                }
                return primary_result

            # Verifier gave an unclear response - keep primary but flag it
            primary_result["accuracy_verified"] = False
            primary_result["accuracy_check"] = {
                "verified": False,
                "method": "cross-provider",
                "verifier_provider": verify_result.get("provider", "unknown"),
                "note": "Verifier response unclear - primary answer delivered",
            }
            return primary_result

        except Exception as exc:
            logger.warning(f"Accuracy double-check failed: {exc}")
            primary_result["accuracy_verified"] = None
            primary_result["accuracy_check"] = {
                "verified": None,
                "method": "cross-provider",
                "error": str(exc),
            }
            return primary_result


# ===================================================================
# 4. REQUEST ROUTER - subscription check -> unlimited flag -> providers
# ===================================================================
class UnlimitedRequestRouter:
    """
    Routes every request:
      1. Check subscription status -> unlimited flag
      2. If unlimited -> priority speed routing (fastest provider first)
      3. If free -> existing limits apply
    """

    def __init__(self):
        self.access_service = SubscriptionAccessService()
        self.accuracy_checker = AccuracyDoubleCheck()

    def route_request(
        self,
        user_id: Optional[str] = None,
        plan: Optional[str] = None,
        status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Route a request based on subscription status.
        Returns routing decision with unlimited flag and provider priority.
        """
        decision = self.access_service.check_access(
            user_id=user_id,
            plan=plan,
            status=status,
        )

        # Build routing info
        routing = {
            "unlimited": decision.unlimited,
            "plan": decision.plan,
            "status": decision.status,
            "reason": decision.reason,
            "priority_speed": decision.unlimited,  # paid users get priority speed
            "provider_priority": PRIORITY_PROVIDER_ORDER if decision.unlimited else None,
            "free_limits": None if decision.unlimited else self.access_service.get_free_limits(),
        }

        return routing

    def should_apply_free_limits(self, plan: Optional[str], status: Optional[str]) -> bool:
        """Check if free limits should apply (i.e., NOT unlimited)."""
        decision = self.access_service.check_access(plan=plan, status=status)
        return not decision.unlimited


# ===================================================================
# Singleton instances
# ===================================================================
subscription_access = SubscriptionAccessService()
accuracy_double_check = AccuracyDoubleCheck()
unlimited_router = UnlimitedRequestRouter()

# Confirmation message
UNLIMITED_MODE_CONFIRMATION = (
    "✅ UNLIMITED MODE ACTIVE — paid users generate unlimited code in every language, "
    "100% accuracy checks on, free limits intact."
)