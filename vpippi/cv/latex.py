"""LaTeX -> HTML (pandoc) and LaTeX -> PDF (latexmk) conversion.

Both binaries are external system dependencies (not pip packages) — see
DEPLOY.md for what needs to be installed on the server.

The HTML conversion does not hand the user's whole document to pandoc as-is:
this CV's LaTeX relies on custom macros (\\cvsection, \\cventry) and a
tcolorbox inline highlight (\\hlbox) that pandoc has no way to turn into the
site's actual `cv-row`/`cv-entry-title`/`highlight` markup — the same markup
the hand-authored HTML CVs already use (see cv/base.html), which is what we're
matching here. Instead we:

1. Resolve every \\definecolor/\\colorlet in the source to a plain hex value.
2. Special-case the header (name in \\huge + a run of \\href contact links)
   into the site's `.contact-info` markup with Bootstrap Icons, matched by
   URL (mailto:/linkedin.com/scholar.google.com/...). If the header doesn't
   match that exact shape, it's left alone and flows through the generic
   pandoc path below instead of being silently dropped.
3. Find each top-level \\cvsection{...} / \\cventry{color}{date}{content}
   call ourselves (brace-aware) and replace it with a placeholder marker.
   For \\cventry, the content argument is split at its first top-level line
   break into a title and a description (matching how every entry in this
   CV is written: `\\textcolor{darkgray}{Title} \\\\ \\textcolor{textgray}{Desc}`),
   each independently converted into `cv-entry-title`/`cv-entry-desc` divs.
   The color argument maps to one of the site's existing tier CSS classes
   (work-high/mid/low, edu-*, pub-*, train-*) via _TIER_CLASS_MAP — built by
   inspecting how the hand-authored CV assigned tiers to this document's
   colors — with an inline `--cv-accent` hex fallback for any other LaTeX CV
   using colors outside that map.
4. Run the remaining "skeleton" text (anything outside those macros) through
   pandoc once, and each extracted argument (titles, dates, entry text)
   through pandoc separately, as its own tiny document — this handles
   arbitrary inline LaTeX (\\textcolor, \\href, \\\\ line breaks, bold/italic)
   reliably without pandoc ever needing to understand \\cventry/\\cvsection.
5. \\hlbox{X} is swapped for a placeholder before each such pandoc call and
   spliced back in afterwards as `<span class="highlight">X</span>` — pandoc
   has no concept of it (it's a tcolorbox one-off), so this can't go through
   pandoc's normal macro handling at all.
6. Splice the per-block HTML into the skeleton output in place of each
   placeholder marker.

FontAwesome icon commands (\\fa...) are dropped wherever they still appear
outside the recognized header (pandoc doesn't know them either).
"""
import html
import re
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings


class LatexError(Exception):
    pass


_COLOR_DIRECTIVE_RE = re.compile(
    r'\\definecolor\{(\w+)\}\{HTML\}\{([0-9A-Fa-f]{6})\}'
    r'|\\colorlet\{(\w+)\}\{([^}]+)\}'
)
_FA_ICON_RE = re.compile(r'\\fa[A-Za-z]+')
_EMPTY_COLOR_SPAN_RE = re.compile(r'\\textcolor\{\w+\}\{\s*\}')
_DOCUMENT_ENV_RE = re.compile(r'\\begin\{document\}(.*)\\end\{document\}', re.S)
_P_WRAPPER_RE = re.compile(r'^\s*<p>(.*)</p>\s*$', re.S)
# pandoc's LaTeX->HTML conversion carries \textcolor{name}{...} straight
# through as a literal `style="color: name"` — it does NOT resolve `name`
# against \definecolor. We do that resolution ourselves, once, at the end.
_COLOR_STYLE_RE = re.compile(r'((?:background-)?color):\s*([A-Za-z]\w*)\b')
_TEXTCOLOR_RE = re.compile(r'^\\textcolor\{\w+\}\{')
_HEADER_NAME_RE = re.compile(r'\\huge\s*\\textcolor\{\w+\}\{([^{}]*)\}')
_HREF_RE = re.compile(r'\\href\{([^{}]*)\}\{')
_BLOCK_CMD_RE = re.compile(r'\\(cvsection|cventry)(?![a-zA-Z])')
_HLBOX_RE = re.compile(r'\\hlbox(?![a-zA-Z])')

# Built by inspecting how the hand-authored "main" HTML CV assigned discrete
# CSS tiers to these exact color names — see main.tex's \colorlet definitions
# (we1..we5, pub1..pub3, edu1..edu3, stu1..stu3). Any color name not listed
# here just gets the inline --cv-accent hex fallback instead.
_TIER_CLASS_MAP = {
    'we1': 'work-high', 'we2': 'work-high', 'we3': 'work-mid', 'we4': 'work-mid', 'we5': 'work-low',
    'pub1': 'pub-high', 'pub2': 'pub-low', 'pub3': 'pub-low',
    'edu1': 'edu-high', 'edu2': 'edu-mid', 'edu3': 'edu-low',
    'stu1': 'train-high', 'stu2': 'train-high', 'stu3': 'train-mid',
}

_ICON_RULES = [
    ('mailto:', 'bi-envelope'),
    ('linkedin.com', 'bi-linkedin'),
    ('scholar.google.com', 'bi-mortarboard'),
    ('github.com', 'bi-github'),
    ('twitter.com', 'bi-twitter'),
    ('x.com', 'bi-twitter'),
]


def _icon_for_url(url):
    for needle, icon in _ICON_RULES:
        if needle in url:
            return icon
    return 'bi-link-45deg'


# --- color resolution --------------------------------------------------------

def _hex_to_rgb(hexval):
    return tuple(int(hexval[i:i + 2], 16) for i in (0, 2, 4))


def _rgb_to_hex(rgb):
    return ''.join(f'{max(0, min(255, round(c))):02X}' for c in rgb)


def _resolve_color_expr(expr, colors):
    expr = expr.strip()
    if '!' in expr:
        parts = [p.strip() for p in expr.split('!')]
        if len(parts) == 3:
            a, pct, b = parts
            pct = float(pct)
            rgb_a = _hex_to_rgb(colors.get(a, 'FFFFFF'))
            rgb_b = _hex_to_rgb(colors.get(b, 'FFFFFF'))
            return _rgb_to_hex(pct / 100 * ca + (1 - pct / 100) * cb for ca, cb in zip(rgb_a, rgb_b))
        if len(parts) == 2:
            a, pct = parts
            pct = float(pct)
            rgb_a = _hex_to_rgb(colors.get(a, 'FFFFFF'))
            return _rgb_to_hex(pct / 100 * ca + (1 - pct / 100) * 255 for ca in rgb_a)
    return colors.get(expr, 'CCCCCC')


def _resolve_colors(tex_source):
    colors = {}
    for m in _COLOR_DIRECTIVE_RE.finditer(tex_source):
        if m.group(1):
            colors[m.group(1)] = m.group(2).upper()
        else:
            colors[m.group(3)] = _resolve_color_expr(m.group(4), colors)
    return colors


def _resolve_color_names(html_text, colors):
    def repl(m):
        prop, name = m.group(1), m.group(2)
        if name in colors:
            return f'{prop}: #{colors[name]}'
        return m.group(0)
    return _COLOR_STYLE_RE.sub(repl, html_text)


# --- brace-aware LaTeX scanning ----------------------------------------------

def _read_group(text, i):
    """text[i] must be '{'. Returns (inner_text, index_after_closing_brace)."""
    depth = 0
    start = i
    while i < len(text):
        if text[i] == '{':
            depth += 1
        elif text[i] == '}':
            depth -= 1
            if depth == 0:
                return text[start + 1:i], i + 1
        i += 1
    raise LatexError("Unbalanced braces in LaTeX source.")


def _strip_textcolor(text):
    """If text is exactly \\textcolor{name}{...}, return the inner content."""
    text = text.strip()
    m = _TEXTCOLOR_RE.match(text)
    if not m:
        return text
    inner, end = _read_group(text, m.end() - 1)
    return inner if end == len(text) else text


def _split_first_top_level_linebreak(text):
    """Split at the first \\\\ that isn't nested inside braces."""
    depth = 0
    i = 0
    n = len(text)
    while i < n - 1:
        c = text[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
        elif depth == 0 and c == '\\' and text[i + 1] == '\\':
            return text[:i].strip(), text[i + 2:].strip()
        i += 1
    return text.strip(), ''


def _extract_hlbox(text):
    """Replace \\hlbox{X} with a unique placeholder, returning (text, {token: X})."""
    out = []
    placeholders = {}
    i = 0
    n = 0
    while True:
        m = _HLBOX_RE.search(text, i)
        if not m:
            out.append(text[i:])
            break
        out.append(text[i:m.start()])
        j = m.end()
        while j < len(text) and text[j] in ' \t\n':
            j += 1
        if j >= len(text) or text[j] != '{':
            out.append(text[m.start():m.end()])
            i = m.end()
            continue
        arg, j = _read_group(text, j)
        token = f'HLBOX{n}TOKEN'
        placeholders[token] = arg
        out.append(token)
        n += 1
        i = j
    return ''.join(out), placeholders


def _extract_blocks(body):
    """Replace top-level \\cvsection{..}/\\cventry{..}{..}{..} calls with
    plain-text placeholder markers, returning (blocks, skeleton_text)."""
    blocks = []
    out = []
    i = 0
    while True:
        m = _BLOCK_CMD_RE.search(body, i)
        if not m:
            out.append(body[i:])
            break
        out.append(body[i:m.start()])
        name = m.group(1)
        nargs = 1 if name == 'cvsection' else 3
        j = m.end()
        args = []
        ok = True
        for _ in range(nargs):
            while j < len(body) and body[j] in ' \t\n':
                j += 1
            if j >= len(body) or body[j] != '{':
                ok = False
                break
            arg, j = _read_group(body, j)
            args.append(arg)
        if not ok:
            out.append(body[m.start():m.end()])
            i = m.end()
            continue
        marker = f'PANDOCBLOCK{len(blocks)}MARKER'
        blocks.append({'kind': name, 'args': args})
        # Force blank-line isolation so pandoc always gives the marker its own
        # paragraph, regardless of the source's spacing around the macro call
        # (main.tex, for one, has no blank line after \cvsection{...} before
        # the following paragraph).
        out.append('\n\n' + marker + '\n\n')
        i = j
    return blocks, ''.join(out)


# --- pandoc plumbing ----------------------------------------------------------

def _synthetic_preamble(colors):
    lines = [r'\documentclass{article}', r'\usepackage[utf8]{inputenc}', r'\usepackage{xcolor}', r'\usepackage{hyperref}']
    for name, hexval in colors.items():
        lines.append(rf'\definecolor{{{name}}}{{HTML}}{{{hexval}}}')
    return '\n'.join(lines) + '\n'


def _run_pandoc(stdin_text, timeout=15):
    pandoc_bin = getattr(settings, 'PANDOC_BIN', 'pandoc')
    try:
        result = subprocess.run(
            [pandoc_bin, '--from', 'latex', '--to', 'html5'],
            input=stdin_text, capture_output=True, encoding='utf-8', errors='replace', timeout=timeout,
        )
    except FileNotFoundError:
        raise LatexError(f"pandoc ({pandoc_bin!r}) is not installed on this server.")
    except subprocess.TimeoutExpired:
        raise LatexError("pandoc timed out converting this document.")
    if result.returncode != 0:
        raise LatexError(result.stderr.strip() or f"pandoc exited with status {result.returncode}")
    return result.stdout


def _pandoc_fragment(preamble, latex_text):
    if not latex_text.strip():
        return ''
    html_out = _run_pandoc(preamble + '\\begin{document}\n' + latex_text + '\n\\end{document}\n')
    m = _P_WRAPPER_RE.match(html_out)
    return m.group(1).strip() if m else html_out.strip()


def _convert_fragment(preamble, latex_text):
    """Convert one inline/paragraph-level LaTeX fragment to HTML, honoring
    \\hlbox{...} as the site's `.highlight` span."""
    if not latex_text.strip():
        return ''
    text, placeholders = _extract_hlbox(latex_text)
    out = _pandoc_fragment(preamble, text)
    for token, arg in placeholders.items():
        inner = _pandoc_fragment(preamble, arg)
        out = out.replace(token, f'<span class="highlight">{inner}</span>')
    return out


# --- header (name + contact links) --------------------------------------------

def _build_header_html(header_text):
    """Recognize main.tex's exact header shape — a \\huge name followed by a
    run of \\href contact links — and rebuild it as the site's
    `.contact-info` markup with Bootstrap Icons chosen by URL. Returns None
    if the shape doesn't match, so the caller can fall back to running the
    text through pandoc generically instead of silently dropping it."""
    name_m = _HEADER_NAME_RE.search(header_text)
    hrefs = list(_HREF_RE.finditer(header_text))
    if not name_m or not hrefs:
        return None
    parts = [f'<h1>{html.escape(name_m.group(1).strip())}</h1>']
    rows = []
    for m in hrefs:
        url = m.group(1)
        icon = _icon_for_url(url)
        display = url[len('mailto:'):] if url.startswith('mailto:') else url
        rows.append(
            f'<div class="d-flex align-items-center"><i class="bi {icon} text-secondary me-2 fs-5"></i>'
            f'<a href="{html.escape(url)}" target="_blank">{html.escape(display)}</a></div>'
        )
    parts.append('<div class="contact-info d-flex flex-column gap-2">' + ''.join(rows) + '</div>')
    return ''.join(parts)


# --- top-level conversion -------------------------------------------------------

def latex_to_html(tex_source):
    if not tex_source.strip():
        return ''

    colors = _resolve_colors(tex_source)
    doc_match = _DOCUMENT_ENV_RE.search(tex_source)
    body = doc_match.group(1) if doc_match else tex_source
    preamble = _synthetic_preamble(colors)

    first_block = _BLOCK_CMD_RE.search(body)
    if first_block:
        header_text, rest = body[:first_block.start()], body[first_block.start():]
    else:
        header_text, rest = body, ''

    header_html = _build_header_html(header_text)
    if header_html is None:
        # Unrecognized header shape — don't risk dropping content, just run
        # it through the normal pandoc path like the rest of the document.
        header_html = ''
        rest = header_text + rest

    rest = _FA_ICON_RE.sub('', rest)
    rest = _EMPTY_COLOR_SPAN_RE.sub('', rest)
    blocks, skeleton = _extract_blocks(rest)

    # The skeleton is arbitrary prose outside any \cventry/\cvsection (e.g.
    # the Technical Summary paragraph in main.tex) and can itself contain
    # \hlbox{...} — pandoc doesn't know that command and silently drops it
    # (argument included), so it needs the same placeholder treatment as a
    # per-block fragment, just applied to the whole multi-paragraph skeleton.
    skeleton, hlbox_placeholders = _extract_hlbox(skeleton)
    body_html = _run_pandoc(preamble + '\\begin{document}\n' + skeleton + '\n\\end{document}\n')
    for token, arg in hlbox_placeholders.items():
        inner = _pandoc_fragment(preamble, arg)
        body_html = body_html.replace(token, f'<span class="highlight">{inner}</span>')

    for index, block in enumerate(blocks):
        marker = f'PANDOCBLOCK{index}MARKER'
        if block['kind'] == 'cvsection':
            title_html = _convert_fragment(preamble, block['args'][0])
            block_html = f'<h2>{title_html}</h2>'
        else:
            color_name = block['args'][0].strip()
            date_arg, content_arg = block['args'][1], block['args'][2]
            hexcolor = colors.get(color_name, 'CCCCCC')
            tier_class = _TIER_CLASS_MAP.get(color_name)
            row_class = 'row g-0 cv-row' + (f' {tier_class}' if tier_class else '')

            date_html = _convert_fragment(preamble, date_arg)

            title_raw, desc_raw = _split_first_top_level_linebreak(content_arg)
            title_html = _convert_fragment(preamble, _strip_textcolor(title_raw))
            desc_html = _convert_fragment(preamble, _strip_textcolor(desc_raw)) if desc_raw else ''
            desc_div = f'<div class="cv-entry-desc">{desc_html}</div>' if desc_html else ''

            block_html = (
                f'<div class="{row_class}" style="--cv-accent:#{hexcolor};">'
                f'<div class="col-md-3 cv-left-col">{date_html}</div>'
                f'<div class="col-md-9 cv-right-col">'
                f'<div class="cv-entry-title">{title_html}</div>'
                f'{desc_div}'
                f'</div></div>'
            )
        body_html = re.sub(r'<p>\s*' + re.escape(marker) + r'\s*</p>', lambda m, h=block_html: h, body_html, count=1)

    return _resolve_color_names(header_html + body_html, colors)


def latex_to_pdf(tex_source):
    if not tex_source.strip():
        raise LatexError("No LaTeX source to compile.")
    with tempfile.TemporaryDirectory(prefix='cv-latex-') as tmp:
        tmp_path = Path(tmp)
        tex_path = tmp_path / 'cv.tex'
        tex_path.write_text(tex_source, encoding='utf-8')
        latexmk_bin = getattr(settings, 'LATEXMK_BIN', 'latexmk')
        try:
            result = subprocess.run(
                [
                    latexmk_bin, '-pdf', '-interaction=nonstopmode', '-halt-on-error',
                    f'-output-directory={tmp_path}', str(tex_path),
                ],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                timeout=60,
                cwd=tmp_path,
            )
        except FileNotFoundError:
            raise LatexError(f"latexmk ({latexmk_bin!r}) is not installed on this server.")
        except subprocess.TimeoutExpired:
            raise LatexError("LaTeX compilation timed out.")

        pdf_path = tmp_path / 'cv.pdf'
        if result.returncode != 0 or not pdf_path.exists():
            log_path = tmp_path / 'cv.log'
            log_tail = ''
            if log_path.exists():
                log_tail = '\n'.join(log_path.read_text(encoding='utf-8', errors='replace').splitlines()[-40:])
            raise LatexError(log_tail or result.stdout[-4000:] or "LaTeX compilation failed.")

        return pdf_path.read_bytes()
