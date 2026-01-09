/**
 * Safe, minimal Markdown renderer for chat messages.
 *
 * Design goals:
 * - Do NOT allow raw HTML passthrough (prevents XSS with v-html).
 * - Support the subset of Markdown used by AI replies: headings, lists, code fences,
 *   inline code, emphasis, links, paragraphs and line breaks.
 * - Convert special book link format `[[书名:ID]]` into internal links.
 */

function escapeHtml(text) {
  return String(text)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function escapeAttr(text) {
  return escapeHtml(text).replace(/`/g, '&#96;')
}

function sanitizeUrl(rawUrl) {
  const url = String(rawUrl || '').trim()
  if (!url) return null

  // Allow in-app absolute paths and fragment links.
  if (url.startsWith('/') || url.startsWith('#')) return url

  try {
    const parsed = new URL(url)
    const protocol = parsed.protocol.toLowerCase()
    if (protocol === 'http:' || protocol === 'https:' || protocol === 'mailto:' || protocol === 'tel:') {
      return parsed.toString()
    }
  } catch {
    // Ignore invalid URLs.
  }
  return null
}

function renderEmphasis(escapedText) {
  let out = String(escapedText || '')
  out = out.replace(/~~(.+?)~~/g, '<del>$1</del>')
  out = out.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
  out = out.replace(/(^|[^*])\*([^*\s][^*]*?[^*\s])\*(?!\*)/g, '$1<em>$2</em>')
  out = out.replace(/(^|[^_])_([^_\s][^_]*?[^_\s])_(?!_)/g, '$1<em>$2</em>')
  return out
}

function renderInline(rawText) {
  const text = String(rawText || '')

  // Tokenize inline code to avoid parsing markdown inside it.
  const tokens = []
  let lastIndex = 0
  const codeRe = /`([^`]+?)`/g
  let match
  while ((match = codeRe.exec(text)) !== null) {
    const before = text.slice(lastIndex, match.index)
    if (before) tokens.push({ type: 'text', value: before })
    tokens.push({ type: 'code', value: match[1] })
    lastIndex = match.index + match[0].length
  }
  const tail = text.slice(lastIndex)
  if (tail) tokens.push({ type: 'text', value: tail })

  return tokens.map((t) => {
    if (t.type === 'code') {
      return `<code>${escapeHtml(t.value)}</code>`
    }

    const raw = String(t.value || '')
    const replacements = new Map()
    let cursor = 0
    let replaced = ''
    let replacementIndex = 0
    const token = (i) => `\uFFF0AILINK${i}\uFFF1`

    const linkRe = /\[\[([^\]\n:：]+?)\s*[:：]\s*(\d+)\s*\]\]|\[([^\]\n]+)\]\(([^)\n]+)\)/g
    let m
    while ((m = linkRe.exec(raw)) !== null) {
      replaced += raw.slice(cursor, m.index)

      // Book link: [[title:id]]
      if (m[1] && m[2]) {
        const id = String(m[2]).trim()
        const title = String(m[1]).trim()
        const placeholder = token(replacementIndex++)
        const titleHtml = renderEmphasis(escapeHtml(title))
        replacements.set(
          placeholder,
          `<a class="ai-book-link" href="/books/${escapeAttr(id)}/" data-book-id="${escapeAttr(id)}">${titleHtml}</a>`
        )
        replaced += placeholder
      }

      // Markdown link: [label](url)
      if (m[3] && m[4]) {
        const label = String(m[3])
        const rawUrl = String(m[4])
        const safeUrl = sanitizeUrl(rawUrl)

        if (!safeUrl) {
          replaced += `${label} (${rawUrl})`
        } else {
          const placeholder = token(replacementIndex++)
          const labelHtml = renderEmphasis(escapeHtml(label))
          const attrs = safeUrl.startsWith('http')
            ? ' target="_blank" rel="noopener noreferrer"'
            : ''
          replacements.set(
            placeholder,
            `<a href="${escapeAttr(safeUrl)}"${attrs}>${labelHtml}</a>`
          )
          replaced += placeholder
        }
      }

      cursor = m.index + m[0].length
    }

    replaced += raw.slice(cursor)

    let out = renderEmphasis(escapeHtml(replaced))
    for (const [placeholder, html] of replacements.entries()) {
      out = out.split(placeholder).join(html)
    }
    return out
  }).join('')
}

function renderBlockquote(blockLines) {
  const inner = blockLines
    .map((l) => l.replace(/^>\s?/, ''))
    .join('\n')
  const html = renderChatMarkdown(inner)
  return `<blockquote>${html}</blockquote>`
}

export function renderChatMarkdown(content) {
  const text = String(content || '').replace(/\r\n/g, '\n')
  const lines = text.split('\n')

  let htmlParts = []
  let paragraph = []
  let list = null // { type: 'ul'|'ol', items: string[] }
  let codeBlock = null // { lang: string, lines: string[] }
  let blockquote = null // string[]

  const flushParagraph = () => {
    if (paragraph.length === 0) return
    const body = paragraph.map(renderInline).join('<br />')
    htmlParts.push(`<p>${body}</p>`)
    paragraph = []
  }

  const flushList = () => {
    if (!list) return
    const tag = list.type
    const itemsHtml = list.items.map((item) => `<li>${item}</li>`).join('')
    htmlParts.push(`<${tag}>${itemsHtml}</${tag}>`)
    list = null
  }

  const flushCodeBlock = () => {
    if (!codeBlock) return
    const lang = (codeBlock.lang || '').trim()
    const classAttr = lang ? ` class="language-${escapeAttr(lang)}"` : ''
    htmlParts.push(`<pre><code${classAttr}>${escapeHtml(codeBlock.lines.join('\n'))}</code></pre>`)
    codeBlock = null
  }

  const flushBlockquote = () => {
    if (!blockquote) return
    htmlParts.push(renderBlockquote(blockquote))
    blockquote = null
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i]

    // Code fences
    const fence = line.match(/^\s*```([^`\s]+)?\s*$/)
    if (fence) {
      flushParagraph()
      flushList()
      flushBlockquote()
      if (!codeBlock) {
        codeBlock = { lang: fence[1] || '', lines: [] }
      } else {
        flushCodeBlock()
      }
      continue
    }

    if (codeBlock) {
      codeBlock.lines.push(line)
      continue
    }

    // Blockquote
    if (blockquote && !line.startsWith('>')) {
      flushBlockquote()
    }
    if (line.startsWith('>')) {
      flushParagraph()
      flushList()
      blockquote = blockquote || []
      blockquote.push(line)
      continue
    }

    // Blank line
    if (!line.trim()) {
      flushParagraph()
      flushBlockquote()
      continue
    }

    // Headings
    const heading = line.match(/^\s{0,3}(#{1,6})\s+(.+?)\s*$/)
    if (heading) {
      flushParagraph()
      flushList()
      flushBlockquote()
      const level = heading[1].length
      htmlParts.push(`<h${level}>${renderInline(heading[2])}</h${level}>`)
      continue
    }

    // Horizontal rule
    if (/^\s*((-{3,})|(\*{3,})|(_{3,}))\s*$/.test(line)) {
      flushParagraph()
      flushList()
      flushBlockquote()
      htmlParts.push('<hr />')
      continue
    }

    // Lists
    const ul = line.match(/^\s*[-*+]\s+(.+?)\s*$/)
    const ol = line.match(/^\s*\d+\.\s+(.+?)\s*$/)
    if (ul || ol) {
      flushParagraph()
      flushBlockquote()
      const type = ul ? 'ul' : 'ol'
      const itemText = ul ? ul[1] : ol[1]
      if (!list || list.type !== type) {
        flushList()
        list = { type, items: [] }
      }
      list.items.push(renderInline(itemText))
      continue
    } else if (list) {
      flushList()
    }

    // Default: paragraph line
    paragraph.push(line)
  }

  flushParagraph()
  flushList()
  flushCodeBlock()
  flushBlockquote()

  return htmlParts.join('')
}
