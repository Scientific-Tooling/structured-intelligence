(function () {
  function slugify(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "")
      .replace(/-{2,}/g, "-");
  }

  function escapeHtml(text) {
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  }

  function inlineFormat(text) {
    return escapeHtml(text)
      .replace(/`([^`]+)`/g, "<code>$1</code>")
      .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
      .replace(/\*([^*]+)\*/g, "<em>$1</em>")
      .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2">$1</a>');
  }

  function renderMarkdown(markdown) {
    const lines = markdown.replace(/\r\n/g, "\n").split("\n");
    const html = [];
    const headings = [];
    const usedIds = new Map();
    let i = 0;

    function consumeParagraph(start) {
      const parts = [];
      let j = start;
      while (j < lines.length) {
        const line = lines[j];
        if (!line.trim()) break;
        if (/^(#{1,6})\s+/.test(line)) break;
        if (/^[-*]\s+/.test(line)) break;
        if (/^\d+\.\s+/.test(line)) break;
        if (/^```/.test(line)) break;
        parts.push(line.trim());
        j += 1;
      }
      return { next: j, html: "<p>" + inlineFormat(parts.join(" ")) + "</p>" };
    }

    function consumeList(start, ordered) {
      const tag = ordered ? "ol" : "ul";
      const pattern = ordered ? /^\d+\.\s+(.*)$/ : /^[-*]\s+(.*)$/;
      const items = [];
      let j = start;
      while (j < lines.length) {
        const line = lines[j];
        const match = line.match(pattern);
        if (!match) break;
        items.push("<li>" + inlineFormat(match[1].trim()) + "</li>");
        j += 1;
      }
      return { next: j, html: `<${tag}>${items.join("")}</${tag}>` };
    }

    function consumeCodeFence(start) {
      let j = start + 1;
      const block = [];
      while (j < lines.length && !/^```/.test(lines[j])) {
        block.push(lines[j]);
        j += 1;
      }
      return {
        next: Math.min(j + 1, lines.length),
        html:
          '<pre><code>' + escapeHtml(block.join("\n")) + "</code></pre>",
      };
    }

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        i += 1;
        continue;
      }

      if (/^```/.test(trimmed)) {
        const result = consumeCodeFence(i);
        html.push(result.html);
        i = result.next;
        continue;
      }

      const heading = trimmed.match(/^(#{1,6})\s+(.*)$/);
      if (heading) {
        const level = heading[1].length;
        const rawText = heading[2].trim();
        const baseId = slugify(rawText) || "section";
        const count = usedIds.get(baseId) || 0;
        usedIds.set(baseId, count + 1);
        const id = count === 0 ? baseId : `${baseId}-${count + 1}`;
        headings.push({ level, id, text: rawText });
        html.push(`<h${level} id="${id}">${inlineFormat(rawText)}</h${level}>`);
        i += 1;
        continue;
      }

      if (/^\d+\.\s+/.test(trimmed)) {
        const result = consumeList(i, true);
        html.push(result.html);
        i = result.next;
        continue;
      }

      if (/^[-*]\s+/.test(trimmed)) {
        const result = consumeList(i, false);
        html.push(result.html);
        i = result.next;
        continue;
      }

      const paragraph = consumeParagraph(i);
      html.push(paragraph.html);
      i = paragraph.next;
    }

    return { html: html.join("\n"), headings };
  }

  function renderToc(headings) {
    const toc = document.querySelector("[data-toc]");
    if (!toc) return;

    const items = headings.filter((heading) => heading.level === 2 || heading.level === 3);
    if (items.length === 0) {
      toc.innerHTML = "<p>No section headings found.</p>";
      return;
    }

    toc.innerHTML = items
      .map((heading) => {
        const cls = heading.level === 3 ? "toc-link toc-sub" : "toc-link";
        return `<a class="${cls}" href="#${heading.id}">${escapeHtml(heading.text)}</a>`;
      })
      .join("");
  }

  async function main() {
    const article = document.querySelector("[data-manuscript-source]");
    if (!article) return;

    const source = article.getAttribute("data-manuscript-source");
    const response = await fetch(source);
    if (!response.ok) {
      article.innerHTML = "<p>Failed to load manuscript source.</p>";
      return;
    }

    const markdown = await response.text();
    const rendered = renderMarkdown(markdown);
    article.innerHTML = rendered.html;
    renderToc(rendered.headings);
  }

  main().catch((error) => {
    const article = document.querySelector("[data-manuscript-source]");
    if (article) {
      article.innerHTML = `<p>Failed to render manuscript: ${escapeHtml(String(error))}</p>`;
    }
  });
})();
