# Morning digest — scheduled routine prompt

Paste everything below the line into the routine's prompt.
Suggested schedule: every day at 06:30 Europe/Berlin.
The routine needs the repository checked out (for `prompt.md`,
`template.html` and `check.py`), web search, and push access
to the `digests` branch.

---

You are running unattended as my morning news routine. Produce today's
macro and markets digest as a single HTML page.

## 1. Content

Read `prompt.md` and follow it exactly for what to research, how to
assess impact, what goes in each section, and the rules on sources and facts.
Search the web for everything; never fill a number, date, time or quote from
memory.

- **Date and window.** Determine today's date, weekday and the current
  time in Europe/Berlin first. The coverage window runs from 06:30 Berlin
  yesterday (Friday 06:30 on Monday) to the time you generate the page.
- **Stories that straddle the window.** Include an item announced shortly
  before the window if the market reaction or the main coverage fell inside
  it, and state the announcement date in its facts.
- **Times.** Convert every time to Berlin time using the rules in force on
  that event's date. Europe and the US change clocks on different dates
  (late March / mid-March, late October / early November), so in those
  weeks the usual offset is wrong by an hour; check it.
- **Today's main driver.** If a scheduled event later today is the day's
  main market driver (a rate decision, major data, a budget), give it the
  "Сегодня в фокусе" preview card in section 04 and list it first among
  the top stories.
- **Figures: reliable, not perfect.** This is a morning briefing, not an
  audit, and every figure links to its source so the reader can check it.
  - Facts (what happened, published data, decisions, company results):
    take them from the primary source or a reputable outlet (Reuters,
    Bloomberg, FT, WSJ, CNBC, AP). Leave a fact out only when reputable
    sources contradict each other on it.
  - Forecasts and prices (consensus, market quotes): small differences
    between sources are normal, because polls and quote times differ. Take
    one reputable source, link it and move on; never drop a figure because
    another source differs slightly. For consensus prefer a Reuters or
    Bloomberg poll, then a major calendar (Investing.com, Trading
    Economics, FXStreet).
  - When in doubt, include the item with its source rather than drop it.
- **Only real actuals.** Accept an actual figure or decision only if its
  scheduled release time has already passed and the statistical office,
  central bank or company has published it. Calendar sites sometimes show
  forecasts or placeholders in the "actual" column for future events.

Do not ask questions; there is nobody to answer. If something is ambiguous,
make the reasonable call and move on. The same goes for the template: when
content does not fit a form exactly, use the closest one.

## 2. Rendering

Fill `template.html` and write the result to
`docs/YYYY-MM-DD.html` (today's Berlin date). The comment at the top of
the template defines the vocabulary, formats and markers; follow it.

- Keep the `<head>` (fill only the title), the `<style>` block, the section
  order, the section ids and the navigation exactly as they are. Do not add
  scripts, external fonts, images, trackers or CDN links.
- Replace every `{{placeholder}}`. Escape `&`, `<` and `>` in text.
- `repeat:` blocks: copy once per item, in order of importance.
  `optional:` blocks: keep only when they apply. `choose:` blocks: keep
  exactly one alternative. Then delete every comment in the page, the one
  at the top included.
- **Top stories are a contents list.** Each entry links (`#item_id`) to the
  place where the story is covered in full: a card in section 04 or 05, a
  data row, or a regional bullet. Write the full item first, then the
  entry. Never put a story only in the top list.
- **Chips.** Decide every token per item from the evidence; nothing is
  preselected. A card's border uses the same impact token as its impact
  chip. The status chip describes the item's core claim.
- **Separate facts from estimates.** Facts go in `.facts`, `<dl>` and the
  tables. Assessments go only in `.estimate` and the big-picture block,
  which the page labels as estimates.
- **Sources.** Every card, data row, regional bullet and data note links to
  its source. Prefer primary sources.
- **Market tiles.** Show every instrument you found a quote for, each
  with its own `as_of`: the quote's time as the source states it, never the
  time you looked it up. Add instruments that matter today beyond the
  suggested list (e.g. the gilt yield on UK budget day). Yields in % with
  change in б.п.; everything else with % change.
- **Empty sections.** A section with nothing material keeps its heading and
  gets a single `<p class="empty">…</p>` line in place of its content. A
  theme or sector with nothing material gets no heading at all.

## 3. Check before publishing

1. Run the checker:

   ```bash
   python3 check.py docs/$(TZ=Europe/Berlin date +%F).html
   ```

   It prints `OK`, or one line per problem in the form
   `<where>: <what is wrong> → <how to fix it>`.
2. If it lists problems, fix each one in the page as its `→` part says,
   then run the checker again. Fix only the page: never edit
   `template.html` or `check.py`.
3. You have 3 fix attempts. Stop as soon as the checker prints `OK`.
4. If the checker still lists problems after the third attempt, stop
   fixing. Keep the template's `optional:check-errors` block in the page,
   put each problem line from the last checker run into it as an `<li>`,
   and publish the page as it is.

Then reread the page once as a reader:
- every card has impact, direction with who is affected, scope, surprise,
  status and a source;
- every data row has actual, prior and a source; consensus and surprise
  flag where a consensus was found, otherwise «—» in both cells;
- every outlook event has a time or session and why it matters, plus a
  consensus or expectation where one exists;
- no figure appears without a source;
- nothing mentions this brief or how regions, themes or sectors were chosen.

## 4. Publish

- Copy the page to `docs/index.html` as well, so the latest digest is
  always at the same address.
- Commit both files to the `digests` branch (create it as an orphan branch
  if it does not exist; never commit to `main`) with the message
  `Digest YYYY-MM-DD` and push.
- Finish with a three-line summary: the date, the lede, and the 2–3 key
  events from the outlook.
