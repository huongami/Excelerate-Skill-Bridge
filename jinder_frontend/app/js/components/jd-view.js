// Job description view (R4). The text uses a small markup:
//   "## Heading" line      -> a heading (h3)
//   "- bullet" line        -> an item in a list
//   blank line             -> a break between paragraphs
//   any other line         -> text of a paragraph (a line break inside a paragraph stays)
// A text with no headings is shown as plain paragraphs. All text is escaped. The box has a maximum height and a scroll bar,
// and the keyboard can reach it (tabindex 0, role region, a label).
import { esc } from "../core/dom.js";

const HEADING = /^#{1,6}\s+(.+?)\s*#*\s*$/;
const BULLET = /^\s*(?:[-*•])\s+(.*)$/;

/** Turn the markup into blocks: { type: "h", text } | { type: "ul", items: string[] } | { type: "p", text }. */
export function parseJd(description) {
  const lines = String(description ?? "").replace(/\r\n?/g, "\n").split("\n");
  const blocks = [];
  let para = [];
  let list = null;
  const endPara = () => { if (para.length) blocks.push({ type: "p", text: para.join("\n") }); para = []; };
  const endList = () => { if (list) blocks.push({ type: "ul", items: list }); list = null; };
  for (const raw of lines) {
    const line = raw.trimEnd();
    if (!line.trim()) { endPara(); endList(); continue; }
    const head = line.trim().match(HEADING);
    if (head) { endPara(); endList(); blocks.push({ type: "h", text: head[1] }); continue; }
    const item = line.match(BULLET);
    if (item) { endPara(); (list || (list = [])).push(item[1].trim()); continue; }
    endList();
    para.push(line.trim());
  }
  endPara();
  endList();
  return blocks;
}

/**
 * @param {string} description  the JD text with the markup
 * @param {{ label?: string }} o  the accessible name of the box (default "Job description")
 */
export function jdViewHtml(description, { label = "Job description" } = {}) {
  const blocks = parseJd(description);
  const body = blocks.length
    ? blocks.map((b) => (b.type === "h" ? `<h3>${esc(b.text)}</h3>`
      : b.type === "ul" ? `<ul>${b.items.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>`
        : `<p>${esc(b.text)}</p>`)).join("")
    : `<p class="jd-view-empty">There is no description for this job.</p>`;
  return `<section class="jd-view" tabindex="0" role="region" aria-label="${esc(label)}">${body}</section>`;
}
