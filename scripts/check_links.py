#!/usr/bin/env python3

'''
Check documentation links without third-party dependencies.

The checker understands the Docsify routing style used by this repository:

* `/path/to/page` resolves to `docs/path/to/page.md`.
* `/path/to/` resolves to `docs/path/to/README.md`.
* `?id=heading` resolves to a heading anchor in the target Markdown file.

Remote HTTP(S) links are checked with HEAD first, then GET as a fallback.  When
a remote URL contains a fragment, the checker fetches HTML pages and verifies
that the referenced `id` or `name` anchor exists.
'''

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import fnmatch
import html
import html.parser
import os
import posixpath
import re
import socket
import ssl
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

try:
  import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised only on old Python.
  print("Python 3.11 or newer is required: tomllib is part of the standard library.", file=sys.stderr)
  raise SystemExit(2)


DEFAULT_CONFIG: dict[str, Any] = {
    "scan": {
        "paths": ["README.md", "docs"],
        "extensions": [".md", ".html"],
        "exclude": ["docs/assets/**"],
        "docs_root": "docs",
    },
    "http": {
        "timeout": 15,
        "retries": 1,
        "workers": 8,
        "user_agent": "pku-minic-online-doc-link-checker/1.0",
        "accepted_statuses": [401, 403, 429],
        "accepted_status_ranges": [[200, 399]],
        "check_fragments": True,
        "max_fragment_page_bytes": 2_000_000,
    },
    "ignore": [],
}

MARKDOWN_LINK_START_RE = re.compile(r"!?\[")
BARE_URL_RE = re.compile(r"(?:(?:https?:)?//)[^\s<>'\"]+")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
HTML_ID_RE = re.compile(r"\s(?:id|name)\s*=\s*(['\"])(.*?)\1", re.IGNORECASE)

SKIPPED_SCHEMES = {
    "data",
    "file",
    "ftp",
    "irc",
    "ircs",
    "javascript",
    "mailto",
    "tel",
}


@dataclasses.dataclass(frozen=True)
class Link:
  source: Path
  line: int
  column: int
  url: str
  kind: str


@dataclasses.dataclass(frozen=True)
class Issue:
  link: Link
  category: str
  message: str
  status: int | None = None


@dataclasses.dataclass(frozen=True)
class RemoteResult:
  ok: bool
  message: str
  status: int | None = None


class LinkHtmlParser(html.parser.HTMLParser):
  LINK_ATTRS = {
      "a": {"href"},
      "area": {"href"},
      "iframe": {"src"},
      "img": {"src", "srcset"},
      "link": {"href"},
      "script": {"src"},
      "source": {"src", "srcset"},
      "video": {"poster", "src"},
  }

  def __init__(self, source: Path) -> None:
    super().__init__(convert_charrefs=True)
    self.source = source
    self.links: list[Link] = []

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    wanted = self.LINK_ATTRS.get(tag.lower())
    if not wanted:
      return
    line, column = self.getpos()
    for attr, value in attrs:
      if value is None or attr.lower() not in wanted:
        continue
      if attr.lower() == "srcset":
        for url in parse_srcset(value):
          self.links.append(
              Link(self.source, line, column + 1, url, "html-srcset"))
      else:
        self.links.append(Link(self.source, line, column +
                          1, value, f"html-{attr.lower()}"))


class AnchorHtmlParser(html.parser.HTMLParser):
  def __init__(self) -> None:
    super().__init__(convert_charrefs=True)
    self.anchors: set[str] = set()

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    for attr, value in attrs:
      if attr.lower() in {"id", "name"} and value:
        self.anchors.add(value)


@dataclasses.dataclass(frozen=True)
class IgnoreRule:
  reason: str = ""
  url: str | None = None
  url_regex: str | None = None
  path: str | None = None
  path_glob: str | None = None
  line: int | None = None
  category: str | None = None
  status: int | None = None
  statuses: tuple[int, ...] = ()

  def matches(self, link: Link, issue: Issue | None = None) -> bool:
    rel_path = link.source.as_posix()
    if self.url is not None and link.url != self.url and normalize_remote_url(link.url) != self.url:
      return False
    if self.url_regex is not None:
      normalized = normalize_remote_url(link.url)
      if not re.search(self.url_regex, link.url) and not re.search(self.url_regex, normalized):
        return False
    if self.path is not None and rel_path != self.path:
      return False
    if self.path_glob is not None and not fnmatch.fnmatch(rel_path, self.path_glob):
      return False
    if self.line is not None and link.line != self.line:
      return False
    if issue is not None:
      if self.category is not None and issue.category != self.category:
        return False
      if self.status is not None and issue.status != self.status:
        return False
      if self.statuses and issue.status not in self.statuses:
        return False
    return True


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(
      description="Check links in the documentation.")
  parser.add_argument("--config", default="check-links.toml",
                      help="TOML configuration file.")
  parser.add_argument("--root", default=".",
                      help="Repository root. Defaults to the current directory.")
  parser.add_argument("--no-http", action="store_true",
                      help="Skip remote HTTP(S) checks.")
  parser.add_argument("--verbose", action="store_true",
                      help="Print checked link counts.")
  return parser.parse_args()


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
  merged = {key: value.copy() if isinstance(value, dict)
            else value for key, value in base.items()}
  for key, value in override.items():
    if isinstance(value, dict) and isinstance(merged.get(key), dict):
      merged[key] = deep_merge(merged[key], value)
    else:
      merged[key] = value
  return merged


def load_config(root: Path, config_path: str) -> dict[str, Any]:
  path = Path(config_path)
  if not path.is_absolute():
    path = root / path
  if not path.exists():
    return DEFAULT_CONFIG
  with path.open("rb") as file:
    loaded = tomllib.load(file)
  return deep_merge(DEFAULT_CONFIG, loaded)


def load_ignore_rules(config: dict[str, Any]) -> list[IgnoreRule]:
  rules: list[IgnoreRule] = []
  for item in config.get("ignore", []):
    if not isinstance(item, dict):
      raise ValueError("Each [[ignore]] entry must be a TOML table.")
    statuses = item.get("statuses", ())
    if isinstance(statuses, list):
      statuses = tuple(int(status) for status in statuses)
    rules.append(
        IgnoreRule(
            reason=str(item.get("reason", "")),
            url=item.get("url"),
            url_regex=item.get("url_regex"),
            path=item.get("path"),
            path_glob=item.get("path_glob"),
            line=item.get("line"),
            category=item.get("category"),
            status=item.get("status"),
            statuses=statuses,
        )
    )
  return rules


def discover_files(root: Path, config: dict[str, Any]) -> list[Path]:
  scan = config["scan"]
  extensions = set(scan.get("extensions", []))
  excludes = scan.get("exclude", [])
  files: list[Path] = []
  for raw_path in scan.get("paths", []):
    path = root / raw_path
    if path.is_file():
      candidates = [path]
    elif path.is_dir():
      candidates = [candidate for candidate in path.rglob(
          "*") if candidate.is_file()]
    else:
      continue
    for candidate in candidates:
      rel = candidate.relative_to(root)
      rel_posix = rel.as_posix()
      if extensions and candidate.suffix not in extensions:
        continue
      if any(fnmatch.fnmatch(rel_posix, pattern) for pattern in excludes):
        continue
      files.append(rel)
  return sorted(set(files))


def parse_srcset(value: str) -> list[str]:
  urls: list[str] = []
  for item in value.split(","):
    parts = item.strip().split()
    if parts:
      urls.append(parts[0])
  return urls


def is_escaped(text: str, index: int) -> bool:
  backslashes = 0
  cursor = index - 1
  while cursor >= 0 and text[cursor] == "\\":
    backslashes += 1
    cursor -= 1
  return backslashes % 2 == 1


def inline_code_spans(line: str) -> list[tuple[int, int]]:
  spans: list[tuple[int, int]] = []
  index = 0
  while index < len(line):
    if line[index] != "`" or is_escaped(line, index):
      index += 1
      continue
    tick_count = 1
    while index + tick_count < len(line) and line[index + tick_count] == "`":
      tick_count += 1
    marker = "`" * tick_count
    end = line.find(marker, index + tick_count)
    if end == -1:
      break
    spans.append((index, end + tick_count))
    index = end + tick_count
  return spans


def in_any_span(index: int, spans: list[tuple[int, int]]) -> bool:
  return any(start <= index < end for start, end in spans)


def find_matching_square_bracket(line: str, start: int) -> int | None:
  depth = 0
  index = start
  while index < len(line):
    char = line[index]
    if is_escaped(line, index):
      index += 1
      continue
    if char == "[":
      depth += 1
    elif char == "]":
      depth -= 1
      if depth == 0:
        return index
    index += 1
  return None


def find_markdown_destination_end(line: str, start: int) -> int | None:
  depth = 0
  index = start
  while index < len(line):
    char = line[index]
    if is_escaped(line, index):
      index += 1
      continue
    if char == "(":
      depth += 1
    elif char == ")":
      if depth == 0:
        return index
      depth -= 1
    index += 1
  return None


def extract_markdown_destination(inner: str) -> str:
  stripped = inner.strip()
  if not stripped:
    return ""
  if stripped.startswith("<"):
    end = stripped.find(">")
    if end != -1:
      return stripped[1:end].strip()
  for index, char in enumerate(stripped):
    if char.isspace() and not is_escaped(stripped, index):
      return stripped[:index].strip()
  return stripped


def extract_markdown_links_line(source: Path, line_no: int, line: str) -> tuple[list[Link], list[tuple[int, int]]]:
  code_spans = inline_code_spans(line)
  links: list[Link] = []
  url_spans: list[tuple[int, int]] = []
  index = 0
  while index < len(line):
    match = MARKDOWN_LINK_START_RE.search(line, index)
    if match is None:
      break
    opener = match.end() - 1
    if in_any_span(opener, code_spans):
      index = match.end()
      continue
    label_end = find_matching_square_bracket(line, opener)
    if label_end is None or label_end + 1 >= len(line) or line[label_end + 1] != "(":
      index = match.end()
      continue
    destination_start = label_end + 2
    destination_end = find_markdown_destination_end(line, destination_start)
    if destination_end is None:
      index = match.end()
      continue
    inner = line[destination_start:destination_end]
    url = html.unescape(extract_markdown_destination(inner))
    if url:
      links.append(
          Link(source, line_no, destination_start + 1, url, "markdown"))
      url_spans.append((destination_start, destination_end))
    index = match.start() + 1
  return links, url_spans + code_spans


def trim_bare_url(raw: str) -> str:
  trailing = ".,;:"
  url = raw.rstrip(trailing)
  while url.endswith(")") and url.count("(") < url.count(")"):
    url = url[:-1]
  while url.endswith("]") and url.count("[") < url.count("]"):
    url = url[:-1]
  return url


def extract_bare_urls_line(source: Path, line_no: int, line: str, ignored_spans: list[tuple[int, int]]) -> list[Link]:
  links: list[Link] = []
  for match in BARE_URL_RE.finditer(line):
    if in_any_span(match.start(), ignored_spans):
      continue
    url = html.unescape(trim_bare_url(match.group(0)))
    links.append(Link(source, line_no, match.start() + 1, url, "bare-url"))
  return links


def extract_markdown_links(root: Path, source: Path) -> list[Link]:
  path = root / source
  links: list[Link] = []
  in_fence = False
  fence_marker = ""
  for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
    stripped = line.lstrip()
    if in_fence:
      if stripped.startswith(fence_marker):
        in_fence = False
      continue
    if stripped.startswith("```") or stripped.startswith("~~~"):
      in_fence = True
      fence_marker = stripped[:3]
      continue
    markdown_links, ignored_spans = extract_markdown_links_line(
        source, line_no, line)
    links.extend(markdown_links)
    links.extend(extract_bare_urls_line(source, line_no, line, ignored_spans))
  return dedupe_links(links)


def extract_html_links(root: Path, source: Path) -> list[Link]:
  text = (root / source).read_text(encoding="utf-8")
  parser = LinkHtmlParser(source)
  parser.feed(text)
  links = list(parser.links)
  for line_no, line in enumerate(text.splitlines(), start=1):
    links.extend(extract_bare_urls_line(source, line_no, line, []))
  return dedupe_links(links)


def dedupe_links(links: list[Link]) -> list[Link]:
  seen: set[tuple[Path, int, str]] = set()
  result: list[Link] = []
  for link in links:
    key = (link.source, link.line, link.url)
    if key in seen:
      continue
    seen.add(key)
    result.append(link)
  return result


def extract_links(root: Path, files: list[Path]) -> list[Link]:
  links: list[Link] = []
  for source in files:
    if source.suffix == ".md":
      links.extend(extract_markdown_links(root, source))
    elif source.suffix == ".html":
      links.extend(extract_html_links(root, source))
  return links


def normalize_remote_url(url: str) -> str:
  stripped = url.strip()
  if stripped.startswith("//"):
    return "https:" + stripped
  return stripped


def has_skipped_scheme(url: str) -> bool:
  parsed = urllib.parse.urlparse(url)
  return parsed.scheme.lower() in SKIPPED_SCHEMES


def is_remote_url(url: str) -> bool:
  normalized = normalize_remote_url(url)
  return normalized.startswith("http://") or normalized.startswith("https://")


def collect_local_anchors(path: Path) -> set[str]:
  text = path.read_text(encoding="utf-8")
  anchors: set[str] = set()
  if path.suffix == ".html":
    parser = AnchorHtmlParser()
    parser.feed(text)
    anchors.update(parser.anchors)
    return expand_anchor_forms(anchors)

  in_fence = False
  fence_marker = ""
  for line in text.splitlines():
    stripped = line.lstrip()
    if in_fence:
      if stripped.startswith(fence_marker):
        in_fence = False
      continue
    if stripped.startswith("```") or stripped.startswith("~~~"):
      in_fence = True
      fence_marker = stripped[:3]
      continue
    match = HEADING_RE.match(line)
    if match is None:
      continue
    heading = clean_heading(match.group(2))
    anchors.update(anchor_forms(heading))
  anchors.update(match.group(2) for match in HTML_ID_RE.finditer(text))
  return expand_anchor_forms(anchors)


def clean_heading(text: str) -> str:
  text = re.sub(r"\s+#+\s*$", "", text.strip())
  text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"\1", text)
  text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
  text = text.replace("`", "")
  return html.unescape(text).strip()


def anchor_forms(text: str) -> set[str]:
  normalized = unicodedata.normalize("NFC", text.strip())
  lower = normalized.lower()
  hyphenated = re.sub(r"\s+", "-", lower)
  compact_punctuation = re.sub(r"[^\w\u0080-\uffff\s-]", "", lower)
  compact_hyphenated = re.sub(r"\s+", "-", compact_punctuation)
  return expand_anchor_forms({normalized, lower, hyphenated, compact_hyphenated})


def expand_anchor_forms(values: set[str]) -> set[str]:
  result: set[str] = set()
  for value in values:
    if not value:
      continue
    normalized = unicodedata.normalize("NFC", value)
    decoded = urllib.parse.unquote(normalized)
    result.add(normalized)
    result.add(decoded)
    result.add(decoded.lower())
    result.add(urllib.parse.quote(decoded, safe="-_.~"))
  return result


def docsify_candidates(root: Path, docs_root: Path, source: Path, raw_url: str) -> tuple[list[Path], str | None]:
  parsed = urllib.parse.urlparse(raw_url)
  query = urllib.parse.parse_qs(parsed.query)
  anchor = parsed.fragment or first_value(query.get("id"))
  path = urllib.parse.unquote(parsed.path)

  if not path:
    return [root / source], anchor

  if path.startswith("/"):
    base = docs_root / path.lstrip("/")
  else:
    base = (root / source).parent / path
  base = Path(os.path.normpath(base))

  candidates: list[Path]
  if path.endswith("/"):
    candidates = [base / "README.md", base / "index.html"]
  elif Path(path).suffix:
    candidates = [base]
  else:
    candidates = [base.with_suffix(
        ".md"), base / "README.md", base.with_suffix(".html")]
  return candidates, anchor


def first_value(values: list[str] | None) -> str | None:
  if not values:
    return None
  return values[0]


def check_local_link(root: Path, docs_root: Path, link: Link) -> Issue | None:
  candidates, anchor = docsify_candidates(
      root, docs_root, link.source, link.url)
  target = next(
      (candidate for candidate in candidates if candidate.exists()), None)
  if target is None:
    rel_candidates = ", ".join(candidate.relative_to(
        root).as_posix() for candidate in candidates)
    return Issue(link, "local-missing-target", f"target does not exist; tried {rel_candidates}")
  if anchor:
    anchors = collect_local_anchors(target)
    wanted = expand_anchor_forms({anchor})
    if anchors.isdisjoint(wanted):
      rel_target = target.relative_to(root).as_posix()
      return Issue(link, "local-missing-anchor", f"anchor '{urllib.parse.unquote(anchor)}' not found in {rel_target}")
  return None


def status_is_accepted(status: int | None, http_config: dict[str, Any]) -> bool:
  if status is None:
    return False
  if status in set(http_config.get("accepted_statuses", [])):
    return True
  for start, end in http_config.get("accepted_status_ranges", []):
    if int(start) <= status <= int(end):
      return True
  return False


def request_once(url: str, method: str, timeout: float, user_agent: str, read_body: bool, max_bytes: int) -> tuple[int, str, bytes, str]:
  headers = {
      "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
      "User-Agent": user_agent,
  }
  if method == "GET" and not read_body:
    headers["Range"] = "bytes=0-0"
  request = urllib.request.Request(url, headers=headers, method=method)
  with urllib.request.urlopen(request, timeout=timeout) as response:
    status = int(response.getcode())
    content_type = response.headers.get("content-type", "")
    final_url = response.geturl()
    body = response.read(max_bytes + 1) if read_body else response.read(1)
    return status, content_type, body, final_url


def request_with_retries(url: str, method: str, http_config: dict[str, Any], read_body: bool) -> tuple[int, str, bytes, str]:
  timeout = float(http_config.get("timeout", 15))
  retries = int(http_config.get("retries", 1))
  max_bytes = int(http_config.get("max_fragment_page_bytes", 2_000_000))
  user_agent = str(http_config.get(
      "user_agent", DEFAULT_CONFIG["http"]["user_agent"]))
  last_error: Exception | None = None
  for attempt in range(retries + 1):
    try:
      return request_once(url, method, timeout, user_agent, read_body, max_bytes)
    except urllib.error.HTTPError as error:
      body = error.read(max_bytes + 1) if read_body else b""
      return int(error.code), error.headers.get("content-type", ""), body, error.geturl()
    except (urllib.error.URLError, socket.timeout, TimeoutError, ssl.SSLError) as error:
      last_error = error
      if attempt < retries:
        time.sleep(0.5 * (attempt + 1))
  assert last_error is not None
  raise last_error


def check_remote_link(url: str, http_config: dict[str, Any]) -> RemoteResult:
  normalized = normalize_remote_url(url)
  base_url, fragment = urllib.parse.urldefrag(normalized)
  needs_fragment_check = bool(fragment) and bool(
      http_config.get("check_fragments", True))
  try:
    head_status, head_type, _head_body, final_url = request_with_retries(
        base_url, "HEAD", http_config, read_body=False
    )
  except Exception as error:
    try:
      get_status, get_type, get_body, final_url = request_with_retries(
          base_url, "GET", http_config, read_body=needs_fragment_check
      )
      return evaluate_remote_response(
          normalized, fragment, get_status, get_type, get_body, final_url, http_config, needs_fragment_check
      )
    except Exception as get_error:
      return RemoteResult(False, f"request failed: {format_error(get_error)}")

  if needs_fragment_check or not status_is_accepted(head_status, http_config):
    try:
      get_status, get_type, get_body, final_url = request_with_retries(
          base_url, "GET", http_config, read_body=needs_fragment_check
      )
      return evaluate_remote_response(
          normalized, fragment, get_status, get_type, get_body, final_url, http_config, needs_fragment_check
      )
    except Exception as error:
      if status_is_accepted(head_status, http_config):
        return RemoteResult(True, "HEAD succeeded; fragment could not be verified", head_status)
      return RemoteResult(False, f"request failed after HTTP {head_status}: {format_error(error)}", head_status)

  return evaluate_remote_response(
      normalized, fragment, head_status, head_type, b"", final_url, http_config, needs_fragment_check=False
  )


def evaluate_remote_response(
    url: str,
    fragment: str,
    status: int,
    content_type: str,
    body: bytes,
    final_url: str,
    http_config: dict[str, Any],
    needs_fragment_check: bool,
) -> RemoteResult:
  if not status_is_accepted(status, http_config):
    return RemoteResult(False, f"HTTP {status}", status)
  if not needs_fragment_check:
    return RemoteResult(True, "ok", status)
  if status in set(http_config.get("accepted_statuses", [])):
    return RemoteResult(True, f"HTTP {status}; fragment not verified", status)
  if fragment.startswith(":~:text="):
    return RemoteResult(True, "text fragment skipped", status)
  if not is_html_content(content_type, final_url):
    return RemoteResult(True, "non-HTML fragment skipped", status)
  anchors = parse_remote_anchors(body, content_type)
  wanted = expand_anchor_forms({fragment})
  if anchors.isdisjoint(wanted):
    return RemoteResult(False, f"HTTP {status}, but fragment '{urllib.parse.unquote(fragment)}' was not found", status)
  return RemoteResult(True, "ok", status)


def is_html_content(content_type: str, url: str) -> bool:
  lowered = content_type.lower()
  if "text/html" in lowered or "application/xhtml+xml" in lowered:
    return True
  return urllib.parse.urlparse(url).path.endswith((".html", ".htm", "/"))


def parse_remote_anchors(body: bytes, content_type: str) -> set[str]:
  charset = "utf-8"
  match = re.search(r"charset=([^;\s]+)", content_type, flags=re.IGNORECASE)
  if match:
    charset = match.group(1).strip("\"'")
  text = body.decode(charset, errors="ignore")
  parser = AnchorHtmlParser()
  parser.feed(text)
  return expand_anchor_forms(parser.anchors)


def format_error(error: Exception) -> str:
  if isinstance(error, urllib.error.URLError) and error.reason:
    return str(error.reason)
  return str(error)


def filter_ignored_links(links: list[Link], ignore_rules: list[IgnoreRule]) -> list[Link]:
  return [link for link in links if not any(rule.matches(link) for rule in ignore_rules)]


def filter_ignored_issues(issues: list[Issue], ignore_rules: list[IgnoreRule]) -> list[Issue]:
  return [issue for issue in issues if not any(rule.matches(issue.link, issue) for rule in ignore_rules)]


def check_links(root: Path, config: dict[str, Any], no_http: bool) -> tuple[list[Issue], dict[str, int]]:
  files = discover_files(root, config)
  links = extract_links(root, files)
  ignore_rules = load_ignore_rules(config)
  links = filter_ignored_links(links, ignore_rules)
  docs_root = root / config["scan"].get("docs_root", "docs")
  issues: list[Issue] = []
  remote_links: dict[str, list[Link]] = {}

  for link in links:
    url = html.unescape(link.url.strip())
    if not url or has_skipped_scheme(url):
      continue
    if is_remote_url(url):
      if not no_http:
        remote_links.setdefault(normalize_remote_url(url), []).append(link)
      continue
    issue = check_local_link(
        root, docs_root, dataclasses.replace(link, url=url))
    if issue is not None:
      issues.append(issue)

  if remote_links and not no_http:
    http_config = config["http"]
    max_workers = int(http_config.get("workers", 8))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
      future_to_url = {
          executor.submit(check_remote_link, url, http_config): url for url in sorted(remote_links)
      }
      for future in concurrent.futures.as_completed(future_to_url):
        url = future_to_url[future]
        try:
          result = future.result()
        except Exception as error:  # pragma: no cover - defensive guard.
          result = RemoteResult(
              False, f"request failed: {format_error(error)}")
        if result.ok:
          continue
        for link in remote_links[url]:
          issues.append(Issue(link, "remote-http",
                        result.message, result.status))

  issues = filter_ignored_issues(issues, ignore_rules)
  stats = {
      "files": len(files),
      "links": len(links),
      "remote_links": sum(len(items) for items in remote_links.values()),
      "unique_remote_links": len(remote_links),
      "issues": len(issues),
  }
  return sorted(issues, key=lambda issue: (issue.link.source.as_posix(), issue.link.line, issue.link.url)), stats


def print_issues(root: Path, issues: list[Issue]) -> None:
  if not issues:
    print("No broken links found.")
    return
  print(f"Found {len(issues)} broken link(s):")
  for issue in issues:
    location = f"{issue.link.source.as_posix()}:{issue.link.line}:{issue.link.column}"
    print(f"- {location}: {issue.link.url}")
    print(f"  {issue.category}: {issue.message}")


def main() -> int:
  args = parse_args()
  root = Path(args.root).resolve()
  config = load_config(root, args.config)
  try:
    issues, stats = check_links(root, config, args.no_http)
  except ValueError as error:
    print(f"Configuration error: {error}", file=sys.stderr)
    return 2
  print_issues(root, issues)
  if args.verbose:
    print(
        "Checked {files} file(s), {links} link(s), {remote_links} remote occurrence(s) "
        "({unique_remote_links} unique).".format(**stats)
    )
  return 1 if issues else 0


if __name__ == "__main__":
  raise SystemExit(main())
