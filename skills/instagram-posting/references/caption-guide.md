# Instagram caption guide

Instagram is warmer and faster than a professional network feed. Same story, tighter
register: people are on a phone, thumb moving, deciding in one line whether to stop.

## Register

- One idea per post. If it needs three paragraphs, it belongs somewhere else.
- Short lines, one thought each.
- Emoji: yes, 1-3, used as punctuation. Never a row of them.
- Hashtags: 5-10, at the very end after a blank line. Mix niche/community tags with
  topical ones. No block of 30, no hashtag-only captions.
- Tag only the people and accounts the user names.

## Structure

1. **Line 1** — the whole hook: what happened, who is in the photo, what is coming.
2. 2-4 short lines — the story: who/what/where, one concrete detail.
3. **CTA** — a question, a date, "save this", "DM us".
4. Blank line, then hashtags.

## Voice

- First-person plural for an account, first-person singular for a personal profile.
  Match the account, do not blend the two.
- Name things. "Guest: <name>, <company>" beats "a valued guest".
- Small humour is fine; slogans are not.
- Never invent numbers, quotes or names. If the photo does not show it, do not write it.

## Anti-patterns

No "Hey guys", no 30 hashtags, no corporate passive voice, no "details in comments",
no fake urgency, no emoji walls, no engagement-bait ("comment YES if...").

## Length

Sweet spot: 3-6 short lines plus hashtags. Hard cap **2200 characters** — the web
composer rejects anything longer. Hashtags can go in the first comment instead of the
caption; pick one and stay consistent per account.

## Captions and newlines

The web caption editor is a Lexical `contenteditable`. `Input.insertText` inserts text
but drops `\n`, and a synthetic `ClipboardEvent('paste')` fills the DOM without being
committed. For multi-line captions send per-line `Input.insertText` with real
`Enter` key events between lines, then read the field back before publishing — and
verify the caption on the published post (see SKILL.md, "Captions do not survive
publish").

## Story copy (when asked)

A story is a different surface: one line of context, one action (link sticker, poll,
countdown). Keep it under ~8 words per line and never reuse the feed caption.
