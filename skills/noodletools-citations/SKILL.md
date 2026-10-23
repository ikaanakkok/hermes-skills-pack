---
name: noodletools-citations
description: "Use when adding or fixing NoodleTools citations for a school project."
version: 1.0.0
author: hermes-skills-pack contributors
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [noodletools, citations, mla, bibliography, school, research]
    related_skills: [grounded-citations]
---

# NoodleTools citations

NoodleTools (`my.noodletools.com`) is a citation manager sold to schools and libraries. This skill covers the mechanics that matter when building a works-cited: creating a project, picking a citation level, adding sources by type, fixing a wrong type without losing the entry, and exporting or sharing the result. You need your own account through your institution.

## Before you start

- Sign in with your own account through the institution's login (often a Google or Microsoft SSO button on `my.noodletools.com/logon/signin`). Never type passwords into chat, prompts, or logs, and never guess credentials: if a login wall appears, stop and ask the user to sign in.
- Confirm the browser is on `/web2.0/projects.html`. A direct `bibliography.html` URL can bounce back to Projects; if it does, open the project from its row.
- Log each source's URL, accessed date, and the exact quote or page **while** you research. Retro-fitting citations from memory is where wrong dates and dead links come from. See [source collection](references/source-collection.md).

## Create a project

- `button#btnCreateNewProject` opens the `#createProject` dialog.
- `#listDesc` is the project title (NoodleTools truncates at 50 characters).
- Style radios: `#ncMLA`, `#ncAPA`, `#ncCHI` (name `listStyle`). Level radios: `#ncStarter`, `#ncJunior`, `#ncAdvanced` (name `listLevel`).
- `#submitCreateProject` saves; the new project appears at the top of the `button.projectNameDesc` list. Rename it later via the row's `button.optionsBtn` -> Rename (inline input, maxlength 50).
- Open a project by clicking its `button.projectNameDesc` row -> `/web2.0/bibliography.html`.

**Choosing a level.** Advanced is the full MLA 9 / APA 7 / Chicago form set and suits most secondary and university work. Junior is a reduced form set for middle grades; Starter is for early grades. Pick the level your teacher asked for, and pick it *before* entering sources: `Change level` in the row menu re-renders every existing citation and can drop fields the smaller forms do not carry.

## Add a source

1. Click `button#btnCreateNewCitation` (top right). It opens `#modalCreateNewCitation`. The element whose text reads "New Source" is a hidden 0x0 menu item and does nothing.
2. **Where is it?** One of `Database | Website | Print or in-hand | Viewed/heard live | File, app, e-book | Other` (`ul li.citationtab > a` inside `.citationTabs`).
3. **What is it?** The values under the chosen tab in `.tabCationValues` (Website: Web Page, Blog, Video Clip (Online), Report (Technical/Research), Software, Wiki ...; Database: Journal, Magazine, Newspaper, Web Content in Database, Report ...).
4. The type loads its form by AJAX into `#citation-container` (not inside `#citationBodyContainer`). Poll until `#citation-container input` count is greater than 3 before typing.
5. Fill the fields, then click the visible `Save` button (`button.savebtn`). `#okCitationBtn` ("Save anyway") is only the override for an incomplete form - a clean entry should never need it.
6. Verify by reloading `/web2.0/bibliography.html` and reading the rendered citation text plus the source count (`[id^=linkNoteCount_]`).

### Autofill versus typing it in

The new-source dialog can pre-fill from a URL, DOI, ISBN, or title. Use it to save typing, then treat the output as a draft:

- **Type:** a page fetched by URL often lands as Web Page when it is really a Report, a Journal article, or a Database item. Change the type before fixing the fields.
- **Container vs publisher:** vendors routinely put the host site in the publisher slot. The container is where the item lives (site, journal, database, book title); the publisher is who produced it.
- **Date:** autofill often returns a crawl, update, or upload date instead of the publication date.
- When autofill fails or guesses wrong, close it and type the entry by hand. Manual entry is always available and is the dependable path.

### Field map

Selectors below match the 2026 UI. If a form looks different, find fields by their visible label instead.

| What | Element | Notes |
| --- | --- | --- |
| Author of the work | `#source_contributors_1_role/_fname/_mname/_lname/_suffix` | role = Author, Editor, Translator, Compiler |
| Author of the part | `#part_contributors_1_*` | the web page, video, or article itself |
| Interview participant | `#event_contributors_1_*` | role = Interviewee or Interviewer |
| Title of the work | `#source_title` | book, report, whole-site work |
| Title of the part | `#part_title` | page, video, chapter |
| Software / repo name | `#emedia_title` | |
| Container | `#online_sitename` | site, journal, or database name |
| Publisher | `#online_sitepublisher` | leave blank when it repeats the container |
| Database picker | `#library_databases` | auto-fills `#online_sitename`; the value is an editable select2, so a custom vendor casing can be appended |
| URL | `#online_siteurl` | |
| DOI | `#source_doi` | verify it resolves to *this* item |
| Dates | `select#source_publicationmonth/_day/_year` or `select#epub_publicationmonth/_day/_year` | work date vs part/web date |
| Access date | `select#online_accessmonth/_day/_year` | month wants a full name ("September"), day/year numeric |

- Extra contributors: "Add Contributor" appends a row with the next `_2_`, `_3_` suffix. Target the container directly (`#composite_partcontributors button.addContributorBtn`, `#composite_sourcecontributors ...`, `#composite_eventcontributors ...`) and wait about a second between rows. Walking up from `_1_role` to find the button builds doubled underscores and breaks.
- Duplicate ids: `#source_publicationmonth` also matches a wrapper DIV. Always use `select#source_publicationmonth`.

## Fix a wrong source type without deleting it

- Row menu `button.optionsBtn` -> `Edit`. Click the `button` inside the menu item, not the `<li>`; the `<li>` swallows the click and opens nothing.
- Change **Where/What** first, because the switch re-renders the form, then re-enter the metadata the new form drops.
- If the correct type is unreachable from the current one, add the source again with the right type, verify it renders, then delete the wrong copy. Row `Delete` plus its confirm dialog is effectively final - do not delete before the replacement is saved.
- Prefixes are semantic: **event** for interview participants, **part** for the work on the page, **source** for the container. Putting an author in the wrong prefix credits the wrong party in the citation.

### Database items

Cite a subscription-database record with **Where = Database** and the database name (EBSCO, JSTOR, ProQuest, Gale ...) in the container field. The publisher stays the item's own publisher. A record that lists a *related* DOI (poster, preprint, proceedings version) is not the same work: check that the DOI resolves before entering it.

### Common types, condensed

- **Web Page:** `part_contributors_*`, `#part_title`, `#online_sitename`, `#online_sitepublisher` (blank if identical), `#online_siteurl`, `epub_publication*`, `online_access*`.
- **Report (Technical/Research)** under Website: `#source_title`, `#online_sitename`, `#source_publisher` (blank when it repeats the container), `#source_docnumber`, `source_publication*`, `online_access*`. `epub_publication*` is hidden for this type and never saved - fill the `source_publication*` fields instead.
- **Software / code repository:** `#emedia_title` = repo name, `#online_sitename` = GitHub, `#online_siteurl`, `#software_type` = Computer software, `epub_publication*` = creation date, `online_access*`.
- **Video Clip (Online):** `#part_title`, `#online_siteurl`, `#online_sitename`; radio `cliptype_isposted` ("on a site like YouTube") is the default.
- **Lecture, Speech or Reading:** the only branch that credits the speaker as **author** plus the channel as uploader; set `lecture_type=Speech` for talks.
- **Recorded interview:** Website -> Video Clip (Online) -> Citing: Interview; participants in `event_contributors_*`, channel under `source_contributors_1_role=Posted by`.

`#partChangeToItemsTop` (Citing) and `#sourceChangeToItemsTop` (From) are Select2 controls: set the subtype **before** filling metadata, because the change re-renders the form and discards what you typed.

## Notecards

Each source row has `a#createNewNC_<sourceId>`; the panel opens at `#notecardTitle` with `#txtSource` preset to that source. Three Quill editors (`#editor-direct-quotation`, `#editor-paraphrase-or-summary`, `#editor-my-ideas`) keep their text in an inner `.ql-editor`. Save with `#closeNC`, then confirm `#linkNoteCount_<sourceId>` reads `01`: a notecard with no text is not saved, so the counter is the proof. Copy direct quotations verbatim from the source or its transcript - never reconstruct a quote from memory.

## Export the works-cited

- Open the project, then `Print/Export` -> `Formatting Options` (choose the style your assignment uses), then export to **Google Docs** (creates a copy in your Drive) or **Word (.docx)**.
- Prefer the export over retyping: it preserves hanging indents, italics, and alphabetical order.
- Check before submitting: hanging indent on wrapped lines; alphabetical by author surname (by title when no author); container titles italicized and part titles in quotes; title case in titles; `Accessed <date>` on web sources; `et al.` after three or more authors.

## Share with a teacher

The row's `td.collaboratoPanel` -> `#shareProjectBtn` -> `form#shareProjectForm`: `#assgnProject` = the inbox name the teacher gave you, `#userViewableName` = your display name, submit with `#submitShareProject` ("Done"). Verify by reading the row's `.shareInfo` tooltip ("This project is shared with: ..."). Share the single project the assignment needs, not your account.

## UI automation pitfalls

- Try DOM `.click()` first for project buttons, type choices, Add Contributor, and Save. If nothing happens, dispatch `pointerdown`/`pointerup`/`mousedown`/`mouseup` then `.click()`, and verify the expected panel or field appeared instead of trusting the click.
- Set inputs with the native setter: `Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(el, v)` then dispatch `input` and `change`. The shorthand `proto.value.set.call(...)` throws `Illegal invocation`.
- Menus close between calls: open a row menu and click its item inside the **same** script.
- Tabs drift: re-read `location.href` at the start of every action, work only in the tab whose URL contains `bibliography`, and call `Page.bringToFront` before typing into a rich-text editor (background tabs silently drop inserted text).
- Keep each fill self-contained: injected helpers vanish on reload and every save closes the form, so repeat New Source -> Where -> What per source.
