# Deployment notes

## LaTeX CV support

The `cv` app can compile LaTeX-sourced CVs (`CVVariant.source_type == 'latex'`) to HTML
and PDF. This needs two system binaries on the server, in addition to the Python deps in
`requirements.txt`:

- **pandoc** — used for LaTeX → HTML conversion (`vpippi/cv/latex.py`). Prefer the
  official release from https://github.com/jgm/pandoc/releases over an old distro
  package.
- **A TeX distribution with `latexmk`** — used for LaTeX → PDF compilation. On
  Debian/Ubuntu, something like:

  ```sh
  sudo apt-get install texlive-latex-extra texlive-fonts-extra texlive-xetex \
      texlive-luatex latexmk
  ```

  covers the packages the default CV (`main.tex`) uses: `fontawesome5`, `tcolorbox`,
  `tabularx`, `montserrat`, `setspace`, `hyperref`, `geometry`.

Both binaries are invoked via `subprocess`. By default the code just runs `pandoc` /
`latexmk` and expects them on `$PATH`; on a host with no root (see below) set the
`PANDOC_BIN` / `LATEXMK_BIN` env vars in `.env` to their absolute paths instead — no pip
packages are involved either way. If either is missing or misconfigured, LaTeX-sourced
CVs show a visible conversion-error block on the page (see `CVVariant.save()`), and the
PDF download route returns a 503, instead of crashing the site.

### PythonAnywhere (paid plan — Hacker or higher)

No root/apt access, but outbound internet works, so both binaries install as portable,
no-root builds straight into your home directory from a PythonAnywhere Bash console.
Free-tier PythonAnywhere restricts outbound internet to an allowlist that does **not**
cover GitHub/CTAN, so these downloads won't work there — you'd need to fetch the
binaries locally and upload them instead.

1. **pandoc** — grab the current Linux x86-64 tarball from
   https://github.com/jgm/pandoc/releases/latest (asset named
   `pandoc-<version>-linux-amd64.tar.gz`):

   ```sh
   cd ~
   wget https://github.com/jgm/pandoc/releases/download/<version>/pandoc-<version>-linux-amd64.tar.gz
   tar xvzf pandoc-<version>-linux-amd64.tar.gz
   # binary ends up at ~/pandoc-<version>/bin/pandoc
   ```

2. **TinyTeX** (a minimal, no-root TeX Live) plus the packages `main.tex` uses:

   ```sh
   wget -qO- "https://yihui.org/tinytex/install-bin-unix.sh" | sh
   ~/.TinyTeX/bin/x86_64-linux/tlmgr update --self
   ~/.TinyTeX/bin/x86_64-linux/tlmgr install montserrat fontawesome5 tcolorbox tabularx hyperref setspace geometry xcolor
   # latexmk ends up at ~/.TinyTeX/bin/x86_64-linux/latexmk
   ```

3. In your production `.env` (next to `manage.py`'s parent, same file `python-dotenv`
   already loads), set the absolute paths from steps 1–2:

   ```
   PANDOC_BIN=/home/<username>/pandoc-<version>/bin/pandoc
   LATEXMK_BIN=/home/<username>/.TinyTeX/bin/x86_64-linux/latexmk
   ```

4. Reload the web app from the PythonAnywhere dashboard — env var and file changes
   don't take effect until the WSGI worker restarts.
