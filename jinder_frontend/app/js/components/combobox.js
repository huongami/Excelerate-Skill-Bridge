// Searchable dropdown (WAI-ARIA 1.2 combobox with a listbox popup).
// The user types to filter. Arrow keys move, Enter selects, Esc closes the list.
// If `allowCustom` is true, the user can keep a value that is not in the list.
const MAX_RESULTS = 50;

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v === false || v == null) continue;
    if (k === "class") node.className = v;
    else if (k === "text") node.textContent = v;
    else node.setAttribute(k, v === true ? "" : v);
  }
  children.forEach((c) => c != null && node.append(c));
  return node;
}
function svgIcon(id) {
  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("class", "icon");
  svg.setAttribute("aria-hidden", "true");
  const use = document.createElementNS("http://www.w3.org/2000/svg", "use");
  use.setAttribute("href", `icons.svg#${id}`);
  svg.append(use);
  return svg;
}
// Show the matched part of an option in bold (built with text nodes, not innerHTML)
function highlight(text, q) {
  const i = q ? text.toLowerCase().indexOf(q.toLowerCase()) : -1;
  if (i < 0) return [document.createTextNode(text)];
  return [text.slice(0, i), el("mark", { text: text.slice(i, i + q.length) }), text.slice(i + q.length)]
    .map((p) => (typeof p === "string" ? document.createTextNode(p) : p));
}

/**
 * @param {object} cfg
 * id, options, value, placeholder, allowCustom (default true)
 * onChange(value)  — called when the value changes (typing or picking)
 * onPick(value)    — called when the user picks or enters a value
 * clearOnPick      — empty the input after a pick (for multi-value fields such as skills)
 * exclude()        — returns values to hide (for example, skills already added)
 */
export function createCombobox({ id, options, value = "", placeholder = "", allowCustom = true, onChange, onPick, clearOnPick = false, exclude = () => [] }) {
  const listId = `${id}-list`;
  const input = el("input", {
    id, type: "text", class: "text-input combo-input", role: "combobox", value, placeholder,
    autocomplete: "off", spellcheck: "false", "aria-autocomplete": "list", "aria-expanded": "false", "aria-controls": listId,
  });
  const toggle = el("button", { type: "button", class: "combo-toggle", tabindex: "-1", "aria-label": "Show options" }, svgIcon("chevron-down"));
  const list = el("ul", { id: listId, role: "listbox", class: "combo-list", hidden: true });
  const status = el("div", { class: "sr-only", role: "status", "aria-live": "polite" });
  const wrap = el("div", { class: "combo" }, input, toggle, list, status);

  let items = [];
  let active = -1;

  function build() {
    const q = input.value.trim();
    const hidden = new Set(exclude().map((x) => x.toLowerCase()));
    const matches = options
      .filter((o) => !hidden.has(o.toLowerCase()) && (!q || o.toLowerCase().includes(q.toLowerCase())))
      // Options that start with the query come first
      .sort((a, b) => (q ? Number(!a.toLowerCase().startsWith(q.toLowerCase())) - Number(!b.toLowerCase().startsWith(q.toLowerCase())) : 0))
      .slice(0, MAX_RESULTS);
    items = matches.map((o) => ({ value: o, custom: false }));
    const exact = options.some((o) => o.toLowerCase() === q.toLowerCase());
    if (allowCustom && q && !exact && !hidden.has(q.toLowerCase())) items.push({ value: q, custom: true });

    list.replaceChildren(...items.map((it, i) => {
      const li = el("li", { id: `${id}-opt-${i}`, role: "option", class: it.custom ? "combo-option combo-custom" : "combo-option", "aria-selected": String(i === active) });
      if (it.custom) li.append(svgIcon("plus"), document.createTextNode(`Use "${it.value}"`));
      else li.append(...highlight(it.value, q));
      li.addEventListener("mousedown", (e) => e.preventDefault()); // keep focus in the input
      li.addEventListener("click", () => pick(it.value));
      return li;
    }));
    if (!items.length) list.append(el("li", { class: "combo-empty", text: allowCustom ? "Type to add your own" : "No matches. Choose an option from the list." }));
    status.textContent = items.length ? `${items.length} option${items.length === 1 ? "" : "s"} available` : "No options";
    input.setAttribute("aria-activedescendant", active >= 0 ? `${id}-opt-${active}` : "");
    if (active >= 0) list.children[active]?.scrollIntoView({ block: "nearest" });
  }
  const isOpen = () => !list.hidden;
  function open() {
    if (isOpen()) return;
    list.hidden = false;
    input.setAttribute("aria-expanded", "true");
    build();
  }
  function close() {
    list.hidden = true;
    active = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  }
  function pick(v) {
    input.value = clearOnPick ? "" : v;
    onChange && onChange(input.value);
    onPick && onPick(v);
    close();
    input.focus();
  }

  input.addEventListener("input", () => { active = -1; onChange && onChange(input.value); open(); build(); });
  input.addEventListener("click", open);
  input.addEventListener("blur", () => {
    setTimeout(close, 100);
    // Use the exact spelling of a list option if the typed text matches it
    const match = options.find((o) => o.toLowerCase() === input.value.trim().toLowerCase());
    if (match && !clearOnPick && match !== input.value) { input.value = match; onChange && onChange(match); }
  });
  toggle.addEventListener("mousedown", (e) => e.preventDefault());
  toggle.addEventListener("click", () => { if (isOpen()) close(); else { open(); input.focus(); } });
  input.addEventListener("keydown", (e) => {
    if (e.key === "ArrowDown" || e.key === "ArrowUp") {
      e.preventDefault();
      if (!isOpen()) open();
      if (!items.length) return;
      active = e.key === "ArrowDown" ? (active + 1) % items.length : (active <= 0 ? items.length : active) - 1;
      build();
    } else if (e.key === "Enter") {
      if (isOpen() && active >= 0) { e.preventDefault(); pick(items[active].value); }
      else if (input.value.trim() && (clearOnPick || isOpen())) {
        // Enter with no highlighted option keeps the typed text (if custom values are allowed)
        e.preventDefault();
        const typed = input.value.trim();
        const match = options.find((o) => o.toLowerCase() === typed.toLowerCase());
        if (match || allowCustom) pick(match || typed);
      }
    } else if (e.key === "Escape") {
      // Close only the list, not the dialog around it
      if (isOpen()) { e.preventDefault(); e.stopPropagation(); close(); }
    } else if (e.key === "Tab") {
      close();
    }
  });

  return { el: wrap, input, value: () => input.value.trim() };
}

