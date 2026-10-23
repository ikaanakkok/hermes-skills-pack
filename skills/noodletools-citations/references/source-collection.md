# Source collection log

Use this alongside a NoodleTools project so every citation can be rebuilt, verified, or defended later. Start the log before the first search; a bibliography assembled from memory at the end produces wrong dates, dead URLs, and quotes that cannot be checked.

## The log

Keep one row per source. JSON lines, CSV, or a table in a notes app all work; the fields matter more than the format.

```json
{"id": "s01",
 "type": "web-page | journal-article | database-record | report | video | book | interview",
 "title": "exact title as printed on the item",
 "part_title": "page / chapter / video title, when the item sits inside a container",
 "container": "journal, site, database, or book the item lives in",
 "publisher": "who produced it; blank when it repeats the container",
 "authors": [{"first": "", "middle": "", "last": "", "role": "Author"}],
 "published": "2025-10-08",
 "url": "the exact URL, including any ?t= or ?id= parameters",
 "doi": "only if it resolves to this item",
 "accessed": "2026-10-23",
 "quote": "the exact words you plan to use",
 "page": "page or page range for print and PDF sources",
 "summary": "one line in your own words, if you are taking notes",
 "file": "local filename of the downloaded PDF, if any",
 "verified": false}
```

Rules that save real work later:

- **URL and accessed date are captured at the moment of reading.** Copy the address bar rather than re-searching for the page; search rankings and session-scoped links both rot.
- **Quotes are byte-exact.** Copy-paste, then check for smart quotes, missing italics, and broken ligatures. A quote you retyped is a paraphrase, and a paraphrase belongs in a different field than a direct quotation.
- **Record the page even when you might not cite it.** Later you need to prove where a claim came from.
- **One source, one row.** A PDF hosted on two sites is one source with two URLs; a database record and its preprint are two sources.
- **`verified: false` until you have reopened the item.** Reopen before submitting.

## Inventory the live project

Do not trust an older summary of what a project contains; read the project.

```javascript
JSON.stringify([...document.querySelectorAll('tr')]
  .filter(r => r.querySelector('[id^=linkNoteCount_]'))
  .map(r => ({text: r.innerText,
    links: [...r.querySelectorAll('a[href]')]
      .map(a => ({text: a.innerText, url: a.href}))})))
```

Classify the saved rows programmatically (original documents, video links, other web and repository items, personal or offline sources) and reconcile against the log. Rendered citations may carry URLs as plain text with layout line breaks rather than anchors, so fall back to the citation text when `links` is empty. Strip layout whitespace only when reconstructing a wrapped URL; never alter its identifier.

## Retrieve and validate

1. Prefer the original document. For a preprint record, the canonical PDF path (for example `arxiv.org/pdf/<id>`) is stable; an author-hosted copy may serve the same work. Keep the NoodleTools citation as recorded and note the alternate copy rather than silently changing the container.
2. Reject error pages that arrive with a `.pdf` name: require `%PDF-` bytes, run `pdfinfo`, and extract page one with `pdftotext -f 1 -l 1 FILE -` to confirm title and authors. Record URL, size, and page count.
3. Watch versions. An unversioned preprint PDF may be a later revision than the date in the citation; identify the revision you actually hold instead of presenting it as the originally dated one.
4. Leave long video as a link unless the user asked for a file. Do not manufacture a PDF or transcript for an offline interview that has no source file.
5. Package an index that lists every citation and flags unavailable or offline entries, with original download URLs and revision notes. Verify an archive with `ZipFile.testzip()` and compare members against the manifest before calling it complete.

## Transcripts for a video-heavy project

The bibliography is the manifest; do not ask the user to paste links.

1. Enumerate the live rows and classify by type (`Video Clip (Online)` and `Lecture, Speech or Reading` are the video rows). State how many videos exist against the total source count before fetching.
2. Read the video ID from the citation **text**, not from `a[href]`: rendered citations wrap long URLs mid-token (`www.youtube.com/ watch?v=XXXXXXXXXXX`), so strip layout whitespace and match `(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})`. Dropping `&t=` and `&list=` is correct; a transcript starts at the beginning either way.
3. Label each file from the citation's author and title, not the video's current title, so filenames match what a teacher sees in the bibliography.
4. Batch-fetch with the `youtube-content` skill and ship per-video text files plus one index; never paste hundreds of KB of transcript into chat.
5. Report per-video word counts and the total, then name the delivered files. A zero-length fetch is a failure - list the title and ID rather than counting it as done.
