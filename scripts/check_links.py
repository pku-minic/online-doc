#!/usr/bin/env python3

'''
Check if links in the documentation are valid.

The checker understands the Docsify routing style used by this repository:

* `/path/to/page` resolves to `docs/path/to/page.md`.
* `/path/to/` resolves to `docs/path/to/README.md`.
* `?id=heading` resolves to a heading anchor in the target Markdown file.

Remote HTTP(S) links are checked with HEAD first, then GET as a fallback. When
a remote URL contains a fragment, the checker fetches HTML pages and verifies
that the referenced `id` or `name` anchor exists.
'''

import argparse
import asyncio
import dataclasses
import fnmatch
import html
import html.parser
import os
import re
import sys
import tomllib
import unicodedata
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, unquote, urldefrag, urlparse

import httpx
from markdown_it import MarkdownIt
from markdown_it.token import Token


DEFAULT_CONFIG: dict[str, Any] = {
    'scan': {
        'paths': ['README.md', 'docs'],
        'extensions': ['.md', '.html'],
        'exclude': ['docs/assets/**'],
        'docs_root': 'docs',
    },
    'http': {
        'timeout': 15,
        'retries': 1,
        'workers': 8,
        'user_agent': 'pku-minic-online-doc-link-checker/1.0',
        'accepted_statuses': [401, 403, 429],
        'accepted_status_ranges': [[200, 399]],
        'check_fragments': True,
        'max_fragment_page_bytes': 2_000_000,
    },
    'ignore': [],
}

BARE_URL_RE = re.compile(r'(?:(?:https?:)?//)[^\s<>\'"]+')
HTML_ID_RE = re.compile(r'\s(?:id|name)\s*=\s*([\'"])(.*?)\1', re.IGNORECASE)
SKIPPED_SCHEMES = {
    'data',
    'file',
    'ftp',
    'irc',
    'ircs',
    'javascript',
    'mailto',
    'tel',
}

MARKDOWN = MarkdownIt(
    'commonmark', {'html': True, 'linkify': True}).enable('linkify')


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
class RemoteResponse:
  status: int
  content_type: str
  body: bytes
  final_url: str


@dataclasses.dataclass(frozen=True)
class RemoteResult:
  ok: bool
  message: str
  status: int | None = None


@dataclasses.dataclass(frozen=True)
class IgnoreRule:
  reason: str = ''
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
    if issue is None:
      return True
    if self.category is not None and issue.category != self.category:
      return False
    if self.status is not None and issue.status != self.status:
      return False
    if self.statuses and issue.status not in self.statuses:
      return False
    return True


class LinkHtmlParser(html.parser.HTMLParser):
  LINK_ATTRS = {
      'a': {'href'},
      'area': {'href'},
      'iframe': {'src'},
      'img': {'src', 'srcset'},
      'link': {'href'},
      'script': {'src'},
      'source': {'src', 'srcset'},
      'video': {'poster', 'src'},
  }

  def __init__(self, source: Path, base_line: int = 1) -> None:
    super().__init__(convert_charrefs=True)
    self.source = source
    self.base_line = base_line
    self.links: list[Link] = []

  @staticmethod
  def parse_srcset(value: str) -> list[str]:
    return [item.strip().split()[0] for item in value.split(',') if item.strip().split()]

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    wanted = self.LINK_ATTRS.get(tag.lower())
    if not wanted:
      return
    line, column = self.getpos()
    for attr, value in attrs:
      if value is None or attr.lower() not in wanted:
        continue
      kind = f'html-{attr.lower()}'
      for url in self.parse_srcset(value) if attr.lower() == 'srcset' else [value]:
        self.links.append(Link(self.source, self.base_line +
                          line - 1, column + 1, url, kind))


class AnchorHtmlParser(html.parser.HTMLParser):
  def __init__(self) -> None:
    super().__init__(convert_charrefs=True)
    self.anchors: set[str] = set()

  def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
    for attr, value in attrs:
      if attr.lower() in {'id', 'name'} and value:
        self.anchors.add(value)


def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
  merged = {key: value.copy() if isinstance(value, dict)
            else value for key, value in base.items()}
  for key, value in override.items():
    if isinstance(value, dict) and isinstance(merged.get(key), dict):
      merged[key] = deep_merge(merged[key], value)
    else:
      merged[key] = value
  return merged


def load_config(root: Path, config_path: str | None) -> dict[str, Any]:
  if config_path is None:
    return DEFAULT_CONFIG
  path = Path(config_path)
  if not path.is_absolute():
    path = root / path
  if not path.exists():
    raise ValueError(f'configuration file not found: {path}')
  with path.open('rb') as file:
    return deep_merge(DEFAULT_CONFIG, tomllib.load(file))


def load_ignore_rules(config: dict[str, Any]) -> list[IgnoreRule]:
  rules: list[IgnoreRule] = []
  for item in config.get('ignore', []):
    if not isinstance(item, dict):
      raise ValueError('each [[ignore]] entry must be a TOML table.')
    statuses = item.get('statuses', ())
    if isinstance(statuses, list):
      statuses = tuple(int(status) for status in statuses)
    rules.append(IgnoreRule(
        reason=str(item.get('reason', '')),
        url=item.get('url'),
        url_regex=item.get('url_regex'),
        path=item.get('path'),
        path_glob=item.get('path_glob'),
        line=item.get('line'),
        category=item.get('category'),
        status=item.get('status'),
        statuses=statuses,
    ))
  return rules


def discover_files(root: Path, config: dict[str, Any]) -> list[Path]:
  scan: dict[str, Any] = config['scan']
  extensions = set(scan.get('extensions', []))
  excludes = scan.get('exclude', [])
  files: list[Path] = []
  for raw_path in scan.get('paths', []):
    path = root / raw_path
    candidates = [path] if path.is_file(
    ) else [candidate for candidate in path.rglob('*') if candidate.is_file()]
    for candidate in candidates:
      rel = candidate.relative_to(root)
      rel_posix = rel.as_posix()
      if extensions and candidate.suffix not in extensions:
        continue
      if any(fnmatch.fnmatch(rel_posix, pattern) for pattern in excludes):
        continue
      files.append(rel)
  return sorted(set(files))


def line_for(token: Token, fallback: int = 1) -> int:
  return token.map[0] + 1 if token.map else fallback


def column_for(lines: list[str], line: int, needle: str) -> int:
  if line < 1 or line > len(lines):
    return 1
  decoded = html.unescape(needle)
  index = lines[line - 1].find(needle)
  if index == -1:
    index = lines[line - 1].find(decoded)
  return index + 1 if index >= 0 else 1


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


def html_links(source: Path, text: str, base_line: int = 1) -> list[Link]:
  parser = LinkHtmlParser(source, base_line)
  parser.feed(text)
  return parser.links


def trim_bare_url(raw: str) -> str:
  url = raw.rstrip('.,;:')
  while url.endswith(')') and url.count('(') < url.count(')'):
    url = url[:-1]
  while url.endswith(']') and url.count('[') < url.count(']'):
    url = url[:-1]
  return html.unescape(url)


def bare_html_links(source: Path, text: str) -> list[Link]:
  links: list[Link] = []
  for line_no, line in enumerate(text.splitlines(), start=1):
    for match in BARE_URL_RE.finditer(line):
      links.append(Link(source, line_no, match.start() + 1,
                   trim_bare_url(match.group(0)), 'bare-url'))
  return links


def extract_markdown_links(root: Path, source: Path) -> list[Link]:
  text = (root / source).read_text(encoding='utf-8')
  lines = text.splitlines()
  links: list[Link] = []
  for token in MARKDOWN.parse(text):
    line = line_for(token)
    if token.type == 'html_block':
      links.extend(html_links(source, token.content, line))
      continue
    if token.type != 'inline':
      continue
    for child in token.children or []:
      child_line = line_for(child, line)
      if child.type == 'html_inline':
        links.extend(html_links(source, child.content, child_line))
      elif child.type == 'link_open':
        url = child.attrGet('href')
        if url:
          links.append(Link(source, child_line, column_for(
              lines, child_line, url), html.unescape(url), 'markdown'))
      elif child.type == 'image':
        url = child.attrGet('src')
        if url:
          links.append(Link(source, child_line, column_for(
              lines, child_line, url), html.unescape(url), 'markdown-image'))
  return dedupe_links(links)


def extract_html_links(root: Path, source: Path) -> list[Link]:
  text = (root / source).read_text(encoding='utf-8')
  return dedupe_links(html_links(source, text) + bare_html_links(source, text))


def extract_links(root: Path, files: list[Path]) -> list[Link]:
  links: list[Link] = []
  for source in files:
    if source.suffix == '.md':
      links.extend(extract_markdown_links(root, source))
    elif source.suffix == '.html':
      links.extend(extract_html_links(root, source))
  return links


def normalize_remote_url(url: str) -> str:
  stripped = url.strip()
  return 'https:' + stripped if stripped.startswith('//') else stripped


def has_skipped_scheme(url: str) -> bool:
  return urlparse(url).scheme.lower() in SKIPPED_SCHEMES


def is_remote_url(url: str) -> bool:
  return normalize_remote_url(url).startswith(('http://', 'https://'))


def inline_text(token: Token) -> str:
  if not token.children:
    return token.content
  return ''.join(child.content for child in token.children if child.type in {'code_inline', 'text', 'image'})


def expand_anchor_forms(values: set[str]) -> set[str]:
  result: set[str] = set()
  for value in values:
    if not value:
      continue
    decoded = unquote(unicodedata.normalize('NFC', value))
    result.update({value, decoded, decoded.lower(),
                  quote(decoded, safe='-_.~')})
  return result


def anchor_forms(text: str) -> set[str]:
  normalized = unicodedata.normalize('NFC', html.unescape(text).strip())
  lower = normalized.lower()
  hyphenated = re.sub(r'\s+', '-', lower)
  compact = re.sub(r'[^\w\u0080-\uffff\s-]', '', lower)
  return expand_anchor_forms({normalized, lower, hyphenated, re.sub(r'\s+', '-', compact)})


def parse_html_anchors(text: str) -> set[str]:
  parser = AnchorHtmlParser()
  parser.feed(text)
  return parser.anchors


def collect_local_anchors(path: Path) -> set[str]:
  text = path.read_text(encoding='utf-8')
  anchors: set[str] = set()
  if path.suffix == '.html':
    anchors.update(parse_html_anchors(text))
  else:
    tokens = MARKDOWN.parse(text)
    for index, token in enumerate(tokens[:-1]):
      if token.type == 'heading_open' and tokens[index + 1].type == 'inline':
        anchors.update(anchor_forms(inline_text(tokens[index + 1])))
    anchors.update(match.group(2) for match in HTML_ID_RE.finditer(text))
  return expand_anchor_forms(anchors)


def first_value(values: list[str] | None) -> str | None:
  return values[0] if values else None


def docsify_candidates(root: Path, docs_root: Path, source: Path, raw_url: str) -> tuple[list[Path], str | None]:
  parsed = urlparse(raw_url)
  anchor = parsed.fragment or first_value(parse_qs(parsed.query).get('id'))
  path = unquote(parsed.path)
  if not path:
    return [root / source], anchor
  base = docs_root / \
      path.lstrip('/') if path.startswith('/') else (root /
                                                     source).parent / path
  base = Path(os.path.normpath(base))
  if path.endswith('/'):
    return [base / 'README.md', base / 'index.html'], anchor
  if Path(path).suffix:
    return [base], anchor
  return [base.with_suffix('.md'), base / 'README.md', base.with_suffix('.html')], anchor


def check_local_link(root: Path, docs_root: Path, link: Link) -> Issue | None:
  candidates, anchor = docsify_candidates(
      root, docs_root, link.source, link.url)
  target = next(
      (candidate for candidate in candidates if candidate.exists()), None)
  if target is None:
    tried = ', '.join(candidate.relative_to(root).as_posix()
                      for candidate in candidates)
    return Issue(link, 'local-missing-target', f'target does not exist; tried {tried}')
  if anchor and collect_local_anchors(target).isdisjoint(expand_anchor_forms({anchor})):
    rel_target = target.relative_to(root).as_posix()
    return Issue(link, 'local-missing-anchor', f'anchor "{unquote(anchor)}" not found in {rel_target}')
  return None


def status_is_accepted(status: int | None, http_config: dict[str, Any]) -> bool:
  if status is None:
    return False
  if status in set(http_config.get('accepted_statuses', [])):
    return True
  return any(int(start) <= status <= int(end) for start, end in http_config.get('accepted_status_ranges', []))


async def request_once(client: httpx.AsyncClient, url: str, method: str, http_config: dict[str, Any], read_body: bool) -> RemoteResponse:
  headers = {'Range': 'bytes=0-0'} if method == 'GET' and not read_body else None
  max_bytes = int(http_config.get('max_fragment_page_bytes', 2_000_000))
  async with client.stream(method, url, headers=headers) as response:
    body = b''
    if read_body:
      async for chunk in response.aiter_bytes():
        body += chunk
        if len(body) > max_bytes:
          body = body[:max_bytes]
          break
    return RemoteResponse(
        response.status_code,
        response.headers.get('content-type', ''),
        body,
        str(response.url),
    )


async def request_with_retries(client: httpx.AsyncClient, url: str, method: str, http_config: dict[str, Any], read_body: bool) -> RemoteResponse:
  retries = int(http_config.get('retries', 1))
  last_error: Exception | None = None
  for attempt in range(retries + 1):
    try:
      return await request_once(client, url, method, http_config, read_body)
    except httpx.HTTPError as error:
      last_error = error
      if attempt < retries:
        await asyncio.sleep(0.5 * (attempt + 1))
  assert last_error is not None
  raise last_error


def is_html_content(content_type: str, url: str) -> bool:
  lowered = content_type.lower()
  return 'text/html' in lowered or 'application/xhtml+xml' in lowered or urlparse(url).path.endswith(('.html', '.htm', '/'))


def parse_remote_anchors(response: RemoteResponse) -> set[str]:
  charset = 'utf-8'
  match = re.search(r'charset=([^;\s]+)',
                    response.content_type, flags=re.IGNORECASE)
  if match:
    charset = match.group(1).strip('"\'')
  return expand_anchor_forms(parse_html_anchors(response.body.decode(charset, errors='ignore')))


def evaluate_remote_response(fragment: str, response: RemoteResponse, http_config: dict[str, Any], needs_fragment: bool) -> RemoteResult:
  if not status_is_accepted(response.status, http_config):
    return RemoteResult(False, f'HTTP {response.status}', response.status)
  if not needs_fragment:
    return RemoteResult(True, 'ok', response.status)
  if response.status in set(http_config.get('accepted_statuses', [])):
    return RemoteResult(True, f'HTTP {response.status}; fragment not verified', response.status)
  if fragment.startswith(':~:text=') or not is_html_content(response.content_type, response.final_url):
    return RemoteResult(True, 'fragment skipped', response.status)
  if parse_remote_anchors(response).isdisjoint(expand_anchor_forms({fragment})):
    return RemoteResult(False, f'HTTP {response.status}, but fragment "{unquote(fragment)}" was not found', response.status)
  return RemoteResult(True, 'ok', response.status)


def format_error(error: Exception) -> str:
  return str(error) or error.__class__.__name__


async def check_remote_by_get(
    client: httpx.AsyncClient,
    base_url: str,
    fragment: str,
    http_config: dict[str, Any],
    needs_fragment: bool,
) -> RemoteResult:
  try:
    response = await request_with_retries(client, base_url, 'GET', http_config, needs_fragment)
    return evaluate_remote_response(fragment, response, http_config, needs_fragment)
  except httpx.HTTPError as error:
    return RemoteResult(False, f'request failed: {format_error(error)}')


async def check_remote_link(client: httpx.AsyncClient, url: str, http_config: dict[str, Any]) -> RemoteResult:
  normalized = normalize_remote_url(url)
  base_url, fragment = urldefrag(normalized)
  needs_fragment = bool(fragment) and bool(
      http_config.get('check_fragments', True))
  try:
    head = await request_with_retries(client, base_url, 'HEAD', http_config, False)
  except httpx.HTTPError:
    return await check_remote_by_get(client, base_url, fragment, http_config, needs_fragment)
  if needs_fragment or not status_is_accepted(head.status, http_config):
    try:
      get = await request_with_retries(client, base_url, 'GET', http_config, needs_fragment)
      return evaluate_remote_response(fragment, get, http_config, needs_fragment)
    except httpx.HTTPError as error:
      if status_is_accepted(head.status, http_config):
        return RemoteResult(True, 'HEAD succeeded; fragment could not be verified', head.status)
      return RemoteResult(False, f'request failed after HTTP {head.status}: {format_error(error)}', head.status)
  return evaluate_remote_response(fragment, head, http_config, False)


async def check_remote_links(
    remote_links: dict[str, list[Link]],
    http_config: dict[str, Any],
    verbose: bool,
) -> list[Issue]:
  concurrency = int(http_config.get('workers', 8))
  timeout = httpx.Timeout(float(http_config.get('timeout', 15)))
  headers = {
      'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
      'User-Agent': str(http_config.get('user_agent', DEFAULT_CONFIG['http']['user_agent'])),
  }
  limits = httpx.Limits(max_connections=concurrency,
                        max_keepalive_connections=concurrency)
  semaphore = asyncio.Semaphore(concurrency)

  async with httpx.AsyncClient(follow_redirects=True, timeout=timeout, headers=headers, limits=limits) as client:
    async def one(url: str) -> tuple[str, RemoteResult]:
      async with semaphore:
        if verbose:
          print(f'Checking remote link: {url}...')
        result = await check_remote_link(client, url, http_config)
        if verbose and not result.ok:
          print(f'FAIL: {url}')
        return url, result

    results = await asyncio.gather(*(one(url) for url in sorted(remote_links)))

  issues: list[Issue] = []
  for url, result in results:
    if result.ok:
      continue
    for link in remote_links[url]:
      issues.append(Issue(link, 'remote-http', result.message, result.status))
  return issues


def filter_ignored_links(links: list[Link], ignore_rules: list[IgnoreRule]) -> list[Link]:
  return [link for link in links if not any(rule.matches(link) for rule in ignore_rules)]


def filter_ignored_issues(issues: list[Issue], ignore_rules: list[IgnoreRule]) -> list[Issue]:
  return [issue for issue in issues if not any(rule.matches(issue.link, issue) for rule in ignore_rules)]


def check_links(root: Path, config: dict[str, Any], no_http: bool, verbose: bool) -> tuple[list[Issue], dict[str, int]]:
  files = discover_files(root, config)
  ignore_rules = load_ignore_rules(config)
  links = filter_ignored_links(extract_links(root, files), ignore_rules)
  if verbose:
    print(f'Scanning {len(links)} link(s)...')

  docs_root = root / config['scan'].get('docs_root', 'docs')
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
    if verbose:
      print(f'Checking local link: {url}... ', end='', flush=True)
    issue = check_local_link(root, docs_root,
                             dataclasses.replace(link, url=url))
    if issue is not None:
      issues.append(issue)
    if verbose:
      print('PASS' if issue is None else 'FAIL')

  if remote_links and not no_http:
    issues.extend(asyncio.run(
        check_remote_links(remote_links, config['http'], verbose)))

  issues = filter_ignored_issues(issues, ignore_rules)
  stats = {
      'files': len(files),
      'links': len(links),
      'remote_links': sum(len(items) for items in remote_links.values()),
      'unique_remote_links': len(remote_links),
      'issues': len(issues),
  }
  return sorted(issues, key=lambda issue: (issue.link.source.as_posix(), issue.link.line, issue.link.url)), stats


def print_issues(issues: list[Issue]) -> None:
  if not issues:
    print('No broken links found.')
    return
  print(f'Found {len(issues)} broken link(s):')
  for issue in issues:
    location = f'{issue.link.source.as_posix()}:{issue.link.line}:{issue.link.column}'
    print(f'- {location}: {issue.link.url}')
    print(f'  {issue.category}: {issue.message}')


def main() -> int:
  parser = argparse.ArgumentParser(
      description='Check links in the documentation.')
  parser.add_argument('--config', default=None,
                      help='TOML configuration file.')
  parser.add_argument('--root', default='.',
                      help='Repository root. Defaults to the current directory.')
  parser.add_argument('--no-http', action='store_true',
                      help='Skip remote HTTP(S) checks.')
  parser.add_argument('--verbose', action='store_true',
                      help='Print checked link counts.')
  args = parser.parse_args()

  root = Path(args.root).resolve()
  try:
    config = load_config(root, args.config)
    issues, stats = check_links(root, config, args.no_http, args.verbose)
  except ValueError as error:
    print(f'Configuration error: {error}', file=sys.stderr)
    return 2
  print_issues(issues)
  if args.verbose:
    print(
        'Checked {files} file(s), {links} link(s), {remote_links} remote occurrence(s) '
        '({unique_remote_links} unique).'.format(**stats)
    )
  return 1 if issues else 0


if __name__ == '__main__':
  raise SystemExit(main())
