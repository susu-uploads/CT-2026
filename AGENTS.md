# Agent Rules

## Repository Structure

This repository contains one course for one academic year. Read `COURSE.md` and the relevant `TASK.md` before changing course materials. Keep these instructions about repository operations; place course content in the exported cards.

| File or directory                             | Purpose                                                                                                          |
|-----------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `README.md`                                   | Repository entry point and course title.                                                                         |
| `COURSE.md`                                   | Course page export, including source metadata, descriptions, sections, and links to course elements.             |
| `AGENTS.md`                                   | Instructions for agents maintaining the repository.                                                              |
| `lecture/`                                    | Collection of numbered lecture directories.                                                                      |
| `lecture/lecture-<number>-<english-title>/`   | One or more original files for a lecture.                                                                        |
| `practice/`                                   | Collection of numbered assignment directories.                                                                   |
| `practice/practice-<number>-<english-title>/` | An assignment card, its original attachments, and any existing solution artifacts.                               |
| `TASK.md`                                     | Assignment metadata followed by the description exported from LMS. Required in every practice directory.         |
| `library/`                                    | Optional directory for additional books or reference files supplied by the source.                               |
| `LIBRARY.md`                                  | Bibliography table of reference names and source links at the repository root.                                   |
| Source attachments                            | Original teaching materials downloaded from LMS; preserve their names and contents unless a change is requested. |
| Solution artifacts                            | User-authored files associated with a practice; preserve them when refreshing an export.                         |
| `.cache/`                                     | Temporary caches inside the relevant practice directory.                                                         |
| `.report/`                                    | Temporary report files and images inside the relevant practice directory.                                        |
| `.gitignore`                                  | Rules excluding local and generated files from Git.                                                              |
| `.gitattributes`                              | File attributes, including the Git LFS tracking rules.                                                           |
| `.gitkeep`                                    | Placeholder that keeps an empty example lecture directory in Git; remove it once materials are added.            |

Naming and placement rules:

- Name each course repository and directory `<EnglishAcronym>-<YYYY>`, using only English letters, digits, and hyphens. Derive the acronym from the English course title and omit programme and enrolment prefixes. Keep the approved course code unchanged. 
- Name lecture and practice directories `lecture-<number>-<english-title>` and `practice-<number>-<english-title>`. Use lowercase English words separated by hyphens; retain the source numbering.
- Keep files directly inside their lecture or practice directory. Do not introduce service subdirectories for assignments, solutions, attachments, or links unless requested.
- English directory names do not require translating or renaming the original files.
- Replace or remove example lecture and practice directories when creating a course; do not present them as exported materials.
- If no additional literature is listed, create neither `library` nor `LIBRARY.md`.
- If references are supplied only as names or links, place `LIBRARY.md` at the repository root without creating `library`.
- If a reference list or links are accompanied by book files, place `LIBRARY.md` at the repository root and the files inside `library`. Use a bibliography table with name and source columns.

- The student is Бабушкин Михаил Вадимович; use БабушкинМВ when naming new individual practice results.
- Preserve existing solutions and project-relative paths; do not execute or retrain notebooks during structural changes.
- Use Python 3.12 for the course Python environment (`.venv`) and Docker images. Keep each practice dependency list in its `requirements.txt`; preserve the assignments' LAMP, WordPress, and Flask requirements.

## Export & Metadata

Start every `COURSE.md` and `TASK.md` with YAML frontmatter delimited by `---`. Use exactly four string fields:

| Field    | Meaning                                                                                                             |
|----------|---------------------------------------------------------------------------------------------------------------------|
| `ru`     | Russian name of the course or assignment.                                                                           |
| `en`     | English translation of that name.                                                                                   |
| `code`   | Approved course directory name for a course card, or the containing practice directory name for an assignment card. |
| `origin` | Canonical LMS URL of the exported course page or assignment.                                                        |

- Preserve already confirmed metadata values. Translate names for `en` and directory naming; retain the source language in exported descriptions.
- Empty strings are placeholders in the template only. Fill every field from confirmed source data when creating a course; keep `code` equal to the actual course or practice directory name.
- Copy educational text completely and in source order. Convert HTML to readable Markdown while preserving paragraphs, lists, emphasis, and working links.
- Do not paraphrase, correct grammar, change formulas, or rewrite assessment criteria from the source.
- Export course descriptions, section headings, and course element names with their links. Exclude navigation controls and completion indicators.
- After frontmatter, `TASK.md` contains only the assignment description exported from LMS, including its original headings, assessment criteria, and links. Source identification belongs in the metadata; do not add fixed sections or duplicate it in a separate source section. If the source has no description, leave the body empty.
- Refresh only the requested exported cards. Preserve original attachments, solution artifacts, unrelated user edits, and directory names.
- Exclude personal grades, submitted answers, feedback, comments, and completion status from the exported cards.
- Keep authentication cookies, session identifiers, tokens, and hidden form fields out of repository files and logs.
- If the source cannot be accessed or confirmed, preserve the existing export and report the limitation rather than inventing content.

## Git

- Make the smallest requested change and preserve unrelated working-tree changes. Commit or publish only when requested.
- Keep Git LFS enabled and preserve the tracking rules in `.gitattributes`. Initialize it with `git lfs install --local` when needed; verify that tracked documents have available LFS contents when moving or importing them.
- Keep the template free of LFS objects. Carry its `.gitattributes` into each generated course repository and enable LFS locally before adding source attachments.
- Generate the root `.gitignore` with Toptal using the applicable operating system, editor, and course tool templates in a single response.
- Preserve the generator links and its response byte-for-byte. Do not manually edit generated templates.
- Put custom path exceptions in the `.gitignore` of the relevant practice or lecture, using explicit relative paths. Do not hide all datasets, reports, or images by extension.
- Keep temporary caches and report assets ignored. Use `git check-ignore` to confirm that service files are excluded while cards, source materials, solutions, and required build files remain available to Git.
- Before finishing, review the diff and confirm that only requested files changed.
