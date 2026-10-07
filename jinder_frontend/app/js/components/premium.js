// Premium markers: crown, "Premium" chip, lock badge, and the "Premium feature" dialog.
// Basic user: a locked feature has a gold "Premium" chip with a lock. Premium user: the feature shows as normal.
// The crown is for the account area only (the user block in the menu and Settings).
import { esc, iconHtml } from "../core/dom.js";
import { openModal } from "./modal.js";

/**
 * The crown icon with a text alternative ("Premium").
 * @param {{ decorative?: boolean, label?: string }} o  decorative: true hides it from screen readers (use it when text next to it says Premium)
 */
export function crownIconHtml({ decorative = false, label = "Premium" } = {}) {
  return decorative
    ? `<span class="crown" aria-hidden="true">${iconHtml("i-crown")}</span>`
    : `<span class="crown" role="img" aria-label="${esc(label)}">${iconHtml("i-crown")}</span>`;
}

/** A gold chip. The text is "Premium" unless you give another text. */
export function premiumChipHtml(text = "Premium") {
  return `<span class="chip chip-gold premium-chip">${esc(text)}</span>`;
}

/**
 * The lock badge for a Premium feature that a Basic user cannot use. It is a gold chip with a lock icon and the text "Premium".
 * By default it is a button: a click opens the "Premium feature" dialog (call bindPremiumLocks(root) once on a parent element).
 * With { static: true } it is only a label (use it inside a link or a button, which must not contain a button).
 * @param {string} featureLabel  the name of the feature, for example "Invite talent". Screen readers read it, and the dialog shows it.
 */
export function lockedBadgeHtml(featureLabel, { static: isStatic = false } = {}) {
  const inner = `${iconHtml("i-lock")}<span aria-hidden="true">Premium</span><span class="sr-only">Premium feature: ${esc(featureLabel)}</span>`;
  return isStatic
    ? `<span class="chip chip-gold locked-badge">${inner}</span>`
    : `<button type="button" class="chip chip-gold chip-btn locked-badge" data-premium-lock="${esc(featureLabel)}">${inner}</button>`;
}

/** Open the "Premium feature" dialog. "Go to Settings" opens the plan section. */
export function openPremiumDialog(featureLabel = "This feature") {
  return openModal({
    title: "Premium feature",
    intro: `${featureLabel} is part of Premium. In this demo you can switch your plan in Settings.`,
    submitText: "Go to Settings",
    async onSubmit() { location.hash = "#/settings?section=plan"; return true; },
  });
}

const bound = new WeakSet();

/**
 * One click handler for a whole page: a click on any element with data-premium-lock="Feature name" opens the dialog.
 * Put the attribute on a locked button (it can hold a static lock badge) or use lockedBadgeHtml. Safe to call many times.
 */
export function bindPremiumLocks(root) {
  if (!root || bound.has(root)) return;
  bound.add(root);
  root.addEventListener("click", (e) => {
    const el = e.target.closest("[data-premium-lock]");
    if (!el || !root.contains(el)) return;
    e.preventDefault();
    openPremiumDialog(el.getAttribute("data-premium-lock") || "This feature");
  });
}
