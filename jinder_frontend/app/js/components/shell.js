// App shell for signed-in screens: a fixed left navigation pane that the user can hide (state is saved)
// and a main area. On small screens the pane opens over the content from a menu button.
// V2: there is no "Settings" item. The user block at the bottom is ONE link to Settings. Premium users get a crown and a gold ring.
// "Compare" is in the menu for both roles. A Basic employer sees a small gold lock on it. The compare basket bar is mounted here.
import { h, icon, logoHtml } from "../core/dom.js";
import { api } from "../api/index.js";
import { compareStore } from "../core/compare-store.js";
import { mountCompareTray } from "./compare-tray.js";

const NAV_KEY = "jinder.ui.nav";

export const NAV = {
  candidate: [
    { id: "home", label: "Home", href: "#/home", icon: "home" },
    { id: "jobs", label: "Jobs", href: "#/jobs", icon: "search" },
    { id: "bookmarks", label: "Bookmarks", href: "#/bookmarks", icon: "bookmark" },
    { id: "applications", label: "Applications", href: "#/applications", icon: "inbox" },
    { id: "compare", label: "Compare", href: "#/compare", icon: "columns" },
    { id: "notifications", label: "Notifications", href: "#/notifications", icon: "bell" },
  ],
  recruiter: [
    { id: "home", label: "Home", href: "#/home", icon: "home" },
    { id: "candidates", label: "Talent", href: "#/candidates", icon: "users" },
    { id: "my-jobs", label: "My jobs", href: "#/my-jobs", icon: "briefcase" },
    { id: "compare", label: "Compare", href: "#/compare", icon: "columns", premiumFeature: true },
    { id: "notifications", label: "Notifications", href: "#/notifications", icon: "bell" },
  ],
};

export const initials = (name) => String(name || "?").trim().split(/\s+/).map((p) => p[0]).slice(0, 2).join("").toUpperCase() || "?";

// The last plan that we know, for the signed-in user. It shows the crown at once when the next page opens.
let planCache = null; // { userId, ent }
let live = null;      // { el, apply } of the shell that is on the page now

window.addEventListener("jinder:plan-change", (e) => {
  if (live && live.el.isConnected && e.detail) { planCache = { userId: live.userId, ent: e.detail }; live.apply(e.detail); }
});

/** Update the name, the initials and the alias in the user block after a change in Settings. */
export function updateShellUser(user) {
  const link = document.getElementById("shellUser");
  if (!link || !user) return;
  link.setAttribute("aria-label", `Account settings, ${user.name}`);
  const name = link.querySelector(".sidebar-user-text strong");
  if (name) name.textContent = user.name;
  const av = link.querySelector(".avatar");
  if (av) av.textContent = initials(user.name);
  link.querySelectorAll("[data-shell-alias]").forEach((el) => (el.textContent = user.alias || ""));
}

/** Renders the shell into root and returns the <main> element for the view. */
export function renderShell(root, ctx, activeId) {
  const user = ctx.user;
  const collapsed = localStorage.getItem(NAV_KEY) === "collapsed";
  const items = NAV[user.role] || [];

  const toggle = h("button", {
    type: "button", class: "btn btn-ghost btn-icon sidebar-toggle", "aria-controls": "sidebar",
    "aria-expanded": String(!collapsed), "aria-label": collapsed ? "Show navigation" : "Hide navigation",
    title: collapsed ? "Show navigation" : "Hide navigation",
  }, icon("panel-left"));

  const nav = h("nav", { class: "sidebar-nav", "aria-label": "Main" },
    h("ul", {}, items.map((it) => {
      const a = h("a", { href: it.href, class: "nav-item", "aria-current": it.id === activeId ? "page" : false, title: it.label },
        icon(it.icon), h("span", { class: "nav-label", text: it.label }),
        it.id === "notifications" ? h("span", { class: "nav-badge", "data-unread": true, hidden: true }) : null);
      if (it.premiumFeature) {
        // A Basic employer sees a gold lock. The page still opens and explains the feature.
        const lock = h("span", { class: "nav-premium", "data-nav-lock": true, hidden: true }, icon("i-lock"), h("span", { class: "nav-premium-text", text: "Premium" }));
        a.append(lock);
      }
      return h("li", {}, a);
    })));

  // The user block: one link to Settings. It has the initials, the name and the role. A Premium user also has a crown, a gold ring and a chip.
  const planNote = h("span", { id: "shellPlanNote", class: "sr-only" });
  const premiumChip = h("span", { class: "chip chip-gold premium-chip", text: "Premium", hidden: true });
  const userLink = h("a", {
    href: "#/settings", id: "shellUser", class: "sidebar-user sidebar-user-link", title: "Account settings",
    "aria-label": `Account settings, ${user.name}`, "aria-describedby": "shellPlanNote", "aria-current": activeId === "settings" ? "page" : false,
  },
  h("span", { class: "avatar-wrap" },
    h("span", { class: "avatar", "aria-hidden": "true", text: initials(user.name) }),
    h("span", { class: "avatar-crown", "aria-hidden": "true" }, icon("i-crown"))),
  h("span", { class: "nav-label sidebar-user-text" },
    h("strong", { text: user.name }),
    h("span", { class: "sidebar-chips" },
      h("span", { class: `chip ${user.role === "recruiter" ? "chip-blue" : "chip-pink"}`, text: user.role === "recruiter" ? "Employer" : "Talent" }),
      premiumChip),
    // Candidates see the alias that employers see
    user.role === "candidate" && user.alias ? h("span", { class: "sidebar-alias", title: "Employers see you by this alias" }, "Alias: ", h("span", { "data-shell-alias": true, text: user.alias })) : null),
  planNote);

  const signOut = h("button", { type: "button", class: "nav-item nav-signout", title: "Sign out" }, icon("log-out"), h("span", { class: "nav-label", text: "Sign out" }));
  signOut.addEventListener("click", async () => { await api.auth.logout(); ctx.navigate("/login"); });

  const top = h("div", { class: "sidebar-top" });
  top.innerHTML = logoHtml("#/home", "Jinder home");
  top.append(toggle);

  const sidebar = h("aside", { class: "sidebar", id: "sidebar" }, top, nav, h("div", { class: "sidebar-bottom" }, userLink, signOut));
  const main = h("main", { class: "app-content", id: "main" });
  const menuBtn = h("button", { type: "button", class: "btn btn-ghost btn-icon", "aria-controls": "sidebar", "aria-expanded": "false", "aria-label": "Open navigation" }, icon("menu"));
  const topbar = h("header", { class: "app-topbar" }, menuBtn);
  topbar.insertAdjacentHTML("beforeend", logoHtml("#/home", "Jinder home"));
  const bell = h("a", { href: "#/notifications", class: "btn btn-ghost btn-icon topbar-bell", "aria-label": "Notifications" }, icon("bell"), h("span", { class: "nav-badge", "data-unread": true, hidden: true }));
  topbar.append(bell);
  const scrim = h("div", { class: "sidebar-scrim", hidden: true });
  const appMain = h("div", { class: "app-main" }, topbar, main);
  const shell = h("div", { class: "app-shell", "data-collapsed": String(collapsed) }, sidebar, scrim, appMain);

  // Desktop: hide or show the pane, and remember it
  toggle.addEventListener("click", () => {
    const now = shell.dataset.collapsed !== "true";
    shell.dataset.collapsed = String(now);
    localStorage.setItem(NAV_KEY, now ? "collapsed" : "expanded");
    toggle.setAttribute("aria-expanded", String(!now));
    toggle.setAttribute("aria-label", now ? "Show navigation" : "Hide navigation");
    toggle.title = toggle.getAttribute("aria-label");
  });
  // Mobile: open the pane over the content
  const setMobile = (open) => {
    shell.classList.toggle("nav-open", open);
    menuBtn.setAttribute("aria-expanded", String(open));
    scrim.hidden = !open;
    if (open) nav.querySelector("a")?.focus();
  };
  menuBtn.addEventListener("click", () => setMobile(true));
  scrim.addEventListener("click", () => setMobile(false));
  sidebar.addEventListener("keydown", (e) => { if (e.key === "Escape" && shell.classList.contains("nav-open")) { setMobile(false); menuBtn.focus(); } });
  nav.addEventListener("click", () => setMobile(false));
  userLink.addEventListener("click", () => setMobile(false));

  root.replaceChildren(shell);

  // The compare basket bar (not on the Compare page: the page has its own list)
  if (activeId !== "compare") mountCompareTray({ host: appMain, shell, kind: compareStore.kindForRole(user.role) });

  // The plan: crown, gold ring and "Premium" chip for a Premium user. A Basic employer sees the lock on "Compare".
  const lockEl = nav.querySelector("[data-nav-lock]");
  const compareLink = lockEl ? lockEl.closest("a") : null;
  const apply = (ent) => {
    const premium = ent.crown === true || ent.plan === "premium";
    userLink.classList.toggle("is-premium", premium);
    premiumChip.hidden = !premium;
    planNote.textContent = premium ? "Premium plan" : "";
    if (lockEl) {
      lockEl.hidden = premium;
      compareLink.title = premium ? "Compare" : "Compare (Premium feature)";
    }
  };
  live = { el: shell, apply, userId: user.id };
  if (planCache && planCache.userId === user.id) apply(planCache.ent);
  api.entitlements.get().then((ent) => { planCache = { userId: user.id, ent }; if (shell.isConnected) apply(ent); }).catch(() => {});

  // Unread count on the Notifications item and the bell (text, not only a dot)
  const setUnread = (n) => {
    shell.querySelectorAll("[data-unread]").forEach((b) => { b.hidden = !n; b.textContent = n > 99 ? "99+" : String(n); });
    const label = n ? `Notifications, ${n} unread` : "Notifications";
    shell.querySelectorAll('a[href="#/notifications"]').forEach((a) => a.setAttribute("aria-label", label));
  };
  const onCount = (e) => (shell.isConnected ? setUnread(e.detail.unread) : window.removeEventListener("jinder:notifications", onCount));
  window.addEventListener("jinder:notifications", onCount);
  api.notifications.list().then((r) => setUnread(r.unread)).catch(() => {});
  return main;
}
