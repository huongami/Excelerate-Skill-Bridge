// Notifications ("/notifications") for both roles (Feature 7 AC1–AC3). In-app only; email events show a demo line.
import { iconHtml as icon, esc, announce } from "../core/dom.js";
import { api } from "../api/index.js";

const ICON = { new_application: "inbox", interview_slots: "calendar", slot_chosen: "calendar", slot_confirmed: "calendar", offer: "star", offer_reply: "star", result: "check", status: "clock", feedback: "send", contacted: "send", contact_declined: "x", job_edited: "edit" };
const when = (iso) => new Date(iso).toLocaleString("en-AU", { dateStyle: "medium", timeStyle: "short" });

export async function notificationsView(root, ctx) {
  root.innerHTML = `
    <div class="dash">
      <div class="dash-head"><div><h1>Notifications</h1><p class="dash-sub">Changes to your applications and jobs.</p></div>
        <button type="button" class="btn btn-secondary" data-all hidden>${icon("check")} Mark all as read</button></div>
      <section class="panel"><div data-list><div class="empty" role="status"><p>Loading…</p></div></div></section>
    </div>`;
  const list = root.querySelector("[data-list]");
  const all = root.querySelector("[data-all]");

  async function load() {
    let res;
    try { res = await api.notifications.list(); }
    catch (err) { list.innerHTML = `<div class="empty" role="alert"><p>${esc(err.message)}</p></div>`; return; }
    window.dispatchEvent(new CustomEvent("jinder:notifications", { detail: { unread: res.unread } }));
    all.hidden = !res.unread;
    if (!res.items.length) {
      list.innerHTML = `<div class="empty"><div class="icon-tile accent">${icon("bell")}</div><p>No notifications yet.</p></div>`;
      return;
    }
    list.innerHTML = `<ul class="notif-list">${res.items.map((n) => `
      <li class="notif${n.read ? "" : " unread"}">
        <span class="icon-tile">${icon(ICON[n.type] || "bell")}</span>
        <div class="notif-text">
          ${n.link ? `<a class="job-title-link" href="#${esc(n.link)}" data-open="${esc(n.id)}">${esc(n.title)}</a>` : `<strong>${esc(n.title)}</strong>`}
          ${n.body ? `<p>${esc(n.body)}</p>` : ""}
          <p class="hint">${esc(when(n.createdAt))}${n.email ? " · Email sent (demo)" : ""}${n.read ? "" : ` · <span class="unread-text">Unread</span>`}</p>
        </div>
      </li>`).join("")}</ul>`;
  }
  // Opening a notification marks it as read
  list.addEventListener("click", async (e) => {
    const a = e.target.closest("[data-open]");
    if (!a) return;
    e.preventDefault();
    try { await api.notifications.markRead([a.dataset.open]); } catch { /* open the link anyway */ }
    ctx.navigate(a.getAttribute("href").slice(1));
  });
  all.addEventListener("click", async () => {
    all.disabled = true;
    try { await api.notifications.markRead([]); announce("All notifications are marked as read."); await load(); }
    finally { all.disabled = false; }
  });
  await load();
}
