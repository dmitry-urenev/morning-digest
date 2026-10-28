#!/usr/bin/env python3
"""Validate a rendered digest page against template.html.

Usage: python3 check.py PAGE.html
Prints "OK" and exits 0, or prints one line per problem and exits 1.
Each problem line reads: <where>: <what is wrong> → <how to fix it in the page>.
"""

import html
import re
import sys
from pathlib import Path

TEMPLATE = Path(__file__).with_name("template.html")

SECTION_IDS = [
    "top-stories", "markets", "data", "policy",
    "companies", "regions", "big-picture", "outlook",
]

# token -> label; None means the token has no visible label to check.
VOCAB = {
    "impact": {"high": "высокое", "medium": "среднее", "low": "низкое"},
    "direction": {"positive": "Позитив", "negative": "Негатив", "mixed": "Смешанно"},
    "status": {"confirmed": "Подтверждено", "reported": "По данным СМИ", "rumor": "Слухи"},
    "surprise": {"above": "▲ Выше", "below": "▼ Ниже", "inline": "= В линию"},
    "trend": {
        "in-trend": "В русле тренда сектора",
        "against-trend": "Против тренда сектора",
        "unclear-trend": "Тренд сектора неоднозначен",
    },
}
UNLABELLED_TOKENS = {"up", "down", "flat", "key", "normal", "preview", "session"}
TOKEN_GROUP = {tok: group for group, labels in VOCAB.items() for tok in labels}
ALLOWED_TOKENS = set(TOKEN_GROUP) | UNLABELLED_TOKENS


def text_of(fragment: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", "", fragment)).split())


def style_block(doc: str) -> str:
    m = re.search(r"<style>(.*?)</style>", re.sub(r"<!--.*?-->", "", doc, flags=re.S), re.S)
    return m.group(1).strip() if m else ""


def line_of(doc: str, pos: int) -> int:
    return doc.count("\n", 0, pos) + 1


def without_error_block(page: str) -> str:
    """Blank out the published-with-problems block, keeping line numbers intact."""
    return re.sub(r'<aside class="check-errors".*?</aside>',
                  lambda m: "\n" * m.group(0).count("\n"), page, flags=re.S)


def check(page: str, template: str) -> list[str]:
    errors: list[str] = []
    page = without_error_block(page)

    def problem(where: str, what: str, fix: str) -> None:
        errors.append(f"{where}: {what} → {fix}")

    def at(pos: int) -> str:
        return f"line {line_of(page, pos)}"

    for m in re.finditer(r"\{\{[^}]*\}\}", page):
        problem(at(m.start()), f"unfilled placeholder {m.group(0)}",
                "fill it, or delete the element it belongs to if there is no content for it")
    for m in re.finditer(r"<!--", page):
        problem(at(m.start()), "template comment left in the page", "delete the whole comment")
    for pattern in (r"<script", r"<link\b", r"<img\b", r"<iframe", r"<[^>]*\ssrc="):
        for m in re.finditer(pattern, page, re.I):
            problem(at(m.start()), f"external resource or script ({m.group(0)[:30]})", "delete it")

    if style_block(page) != style_block(template):
        problem("<style>", "differs from the template",
                "replace it with the <style> block copied unchanged from template.html")

    found_sections = re.findall(r'<section id="([^"]+)"', page)
    if found_sections != SECTION_IDS:
        problem("sections", f"found {found_sections}",
                f"keep exactly these sections in this order: {SECTION_IDS}")

    nav = lambda doc: re.findall(r'<nav class="toc".*?</nav>', doc, re.S)
    if nav(page) != nav(template):
        problem("<nav>", "differs from the template",
                "replace it with the <nav> block copied unchanged from template.html")

    ids = re.findall(r'\sid="([^"]+)"', page)
    for dup in sorted({i for i in ids if ids.count(i) > 1}):
        problem(f'id "{dup}"', "used more than once", "give every item its own item_id")
    for i in ids:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", i):
            problem(f'id "{i}"', "invalid", "use only lowercase latin letters, digits and hyphens")
    for m in re.finditer(r'href="#([^"]*)"', page):
        if m.group(1) not in ids:
            problem(at(m.start()), f'link to missing anchor "#{m.group(1)}"',
                    "point it at the item_id of an existing item, or delete the entry with the link")

    top = re.search(r'<section id="top-stories">(.*?)</section>', page, re.S)
    if top and '<p class="empty">' not in top.group(1):
        entries = re.findall(r"<li\b.*?</li>", top.group(1), re.S)
        if not 3 <= len(entries) <= 8:
            problem("top stories", f"{len(entries)} entries", "list the 3 to 8 most important items")
        for entry in entries:
            name = f'top story "{text_of(entry)[:40]}"'
            link = re.search(r'href="#([^"]+)"', entry)
            if not link:
                problem(name, "does not link to an item below",
                        "link it to the item_id of its full item, or delete the entry")
                continue
            dot = re.search(r'class="is-(high|medium|low)"', entry)
            target = re.search(r'\sid="%s"' % re.escape(link.group(1)), page)
            if dot and target:
                rest = page[target.end():]
                end = re.search(r"</article>|</tr>|</li>", rest)
                impact = re.search(r'<span class="tag is-(high|medium|low)">', rest[: end.start() if end else 0])
                if impact and impact.group(1) != dot.group(1):
                    problem(name, f"is is-{dot.group(1)} but the item it links to is is-{impact.group(1)}",
                            "use the same impact token and label in the entry as in the item")

    for m in re.finditer(r'<a\s[^>]*href="https?://[^"]*"[^>]*>', page):
        tag = m.group(0)
        if 'target="_blank"' not in tag or 'rel="noopener"' not in tag:
            problem(at(m.start()), "external link opens in the same tab",
                    'add target="_blank" rel="noopener" to the <a>')

    for m in re.finditer(r'class="([^"]*)"', page):
        for token in re.findall(r"\bis-([a-z-]+)", m.group(1)):
            if token not in ALLOWED_TOKENS:
                problem(at(m.start()), f'unknown token "is-{token}"',
                        "use a token from the vocabulary in the template's top comment")

    for m in re.finditer(r'<span class="([^"]*\b(?:tag|flag)\b[^"]*)">(.*?)</span>', page, re.S):
        classes, text = m.group(1).split(), text_of(m.group(2))
        if "shift" in classes:
            continue
        for cls in classes:
            token = cls[3:] if cls.startswith("is-") else None
            group = TOKEN_GROUP.get(token or "")
            if not group:
                continue
            label = VOCAB[group][token]
            expected, ok = {
                "impact": (f"«Влияние: {label}» or «{label}»", text in (label, f"Влияние: {label}")),
                "direction": (f"«{label}: <кто>»", text.startswith(f"{label}: ") and len(text) > len(label) + 2),
            }.get(group, (f"«{label}»", text == label))
            if not ok:
                problem(at(m.start()), f'chip "{text}" does not match is-{token}',
                        f"write {expected}, or change the token to the one that fits the text")

    for m in re.finditer(r'<article class="card is-([a-z-]+)"[^>]*>(.*?)</article>', page, re.S):
        token, body = m.group(1), m.group(2)
        where = f'{at(m.start())} card "{text_of(body)[:40]}"'
        if not re.search(r'href="https?://', body):
            problem(where, "has no source link",
                    "add its source link, or delete the card and its top-story entry")
        if token == "preview":
            continue
        impact = re.search(r'<span class="tag is-(high|medium|low)">', body)
        if not impact or impact.group(1) != token:
            problem(where, f"border is-{token} does not match its impact chip",
                    "use the same impact token on the <article> and on the impact chip")
        if '<p class="facts">' not in body or '<div class="estimate">' not in body:
            problem(where, "is missing its facts or its estimate block",
                    "add the missing block from the template")

    for m in re.finditer(r'<tr id="[^"]*">(.*?)</tr>', page, re.S):
        if not re.search(r'href="https?://', m.group(1)):
            problem(f'{at(m.start())} data row "{text_of(m.group(1))[:40]}"', "has no source link",
                    "link the indicator name to its source, or delete the row")
    regions = re.search(r'<section id="regions">(.*?)</section>', page, re.S)
    if regions:
        for m in re.finditer(r"<li\b.*?</li>", regions.group(1), re.S):
            if not re.search(r'href="https?://', m.group(0)):
                problem(f'regional bullet "{text_of(m.group(0))[:40]}"', "has no source link",
                        "add the ↗ source link, or delete the bullet")

    for m in re.finditer(r'<div class="tile is-([a-z]+)">(.*?)<div class="chg">(.*?)</div>', page, re.S):
        move, change = m.group(1), text_of(m.group(3))
        where = f"{at(m.start())} tile"
        sign = change[:1]
        expected = {"up": "+", "down": "−"}.get(move)
        if expected and sign != expected:
            problem(where, f'is-{move} but the change is "{change}"',
                    "set the move token to match the sign: + is up, − is down, below 0,05% or 1 б.п. is flat")
        if move == "flat" and sign not in ("+", "−", "0", "±"):
            problem(where, f'change "{change}" has no sign', "write it with + or −")
        if sign == "-":
            problem(where, f'change "{change}" uses a hyphen', "use the minus sign «−»")

    for m in re.finditer(r'<div class="tile[^"]*">.*?<div class="asof">', page, re.S):
        if m.group(0).count('<div class="tile') > 1:
            problem(f"{at(m.start())} tile", "has no as_of line",
                    "add <div class=\"asof\"> with the quote's time as the source states it")

    outlook = re.search(r'<section id="outlook">(.*?)</section>', page, re.S)
    if outlook and "<li" in outlook.group(1):
        for m in re.finditer(r"<li\b.*?</li>", outlook.group(1), re.S):
            if m.group(0).count('class="time') > 1 or m.group(0).count('class="cons"') > 1:
                problem(f'event "{text_of(m.group(0))[:40]}"', "keeps both choose: alternatives",
                        "keep one time line and one consensus or expectation line")
        key_events = len(re.findall(r'<li class="is-key">', outlook.group(1)))
        if not 2 <= key_events <= 3:
            problem("outlook", f"{key_events} key events",
                    "mark the 2 to 3 most market-moving events is-key and the rest is-normal")

    return errors


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    page = Path(sys.argv[1]).read_text(encoding="utf-8")
    errors = check(page, TEMPLATE.read_text(encoding="utf-8"))
    for error in errors:
        print(error)
    if errors:
        print(f"{len(errors)} problem(s)")
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
