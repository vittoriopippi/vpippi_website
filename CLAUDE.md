# vpippi.com

Django site (`vpippi/`) hosted on PythonAnywhere (see DEPLOY.md). Apps: `cv` (CV variants served at `/` and
`/cv/<slug>/`), `jobs` (job application tracker at `/jobs/`), `assistant` (staff-only Gemini chat at `/assistant/`),
plus a few small ones.

## Live content is NOT in the local database

CVs and job applications live in the **production** SQLite DB on PythonAnywhere. The local
`vpippi/db.sqlite3` is a separate, gitignored copy. Running `manage.py` / the Django shell here only changes the
local copy — never use it to "edit the website's content".

To read or change live content, use the tool API via `tools/site_api.py` (needs `SITE_API_TOKEN` in the repo-root
`.env`; server must have the same value as `ASSISTANT_API_TOKEN`). It runs exactly the tools the chat assistant has,
through `assistant/dispatch.py`, so lock checks and validation are identical.

```
python tools/site_api.py tools                      # list tools + parameters
python tools/site_api.py call list_cv_variants
python tools/site_api.py call get_cv_variant slug=apple --field output.source_content > apple.html
python tools/site_api.py call edit_cv_content slug=apple old_text=@old.txt new_text=@new.txt
python tools/site_api.py call write_cv_content slug=apple source_content=@apple.html
python tools/site_api.py call update_job_application id:=7 status=Interviewing
python tools/site_api.py call delete_cv_variant slug=apple    # only STAGES the delete
python tools/site_api.py pending
python tools/site_api.py confirm 12
```

Argument syntax: `name=text`, `name=@file` (value read from a UTF-8 file — use for CV source and `old_text`/`new_text`),
`name:=json` for non-strings (`is_default:=true`, `id:=3`). `--field output.x` prints one field as plain text.
Always `get_cv_variant` before `edit_cv_content` (the old text must match exactly once). Write tools apply to the live
site immediately.

Rules for Claude using this API:
- Deletes are two-step. **Ask the user before running `confirm` on a staged delete**; never confirm on your own.
- A locked CV (`is_locked`) refuses all writes; there is no unlock tool (only the Django admin). Tell the user instead of working around it.
- Don't dump whole CVs into the conversation unless needed; prefer `--field` and files in a scratch directory.
- Never print or commit the token.

## Code changes and deploy

Code is edited here and pushed to GitHub (`main`). The server then needs `git pull`, `python manage.py migrate`
if there are new migrations, and a web app reload from the PythonAnywhere dashboard. Env/file changes do not take
effect until the reload.

## Misc

- Tests: `cd vpippi && python manage.py test assistant`
- `.env` lives in the repo root (one level above `manage.py`) and is gitignored.
