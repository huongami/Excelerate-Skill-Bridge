// MOCK BACKEND — candidate aliases. The real backend replaces this file.
// Recruiters see a candidate only by alias. An alias must not show a real name or where a person is from.
import { COUNTRIES } from "../../data/reference.js";

// Neutral words only (Feature 1 backlog): no personality adjectives, no colours that describe skin or hair.
const COLOURS = ["Amber", "Azure", "Cobalt", "Coral", "Cyan", "Indigo", "Jade", "Lilac", "Lime", "Mint", "Plum", "Saffron", "Sage", "Slate", "Teal", "Violet"];
const ANIMALS = ["Badger", "Crane", "Dolphin", "Falcon", "Finch", "Fox", "Gecko", "Heron", "Kestrel", "Koala", "Llama", "Lynx", "Otter", "Owl", "Panda", "Puffin", "Robin", "Seal", "Swift", "Wombat"];

// Words that show origin. An alias with one of these words is not accepted.
const ORIGIN_WORDS = [
  ...COUNTRIES,
  "Aboriginal", "African", "American", "Arab", "Asian", "Australian", "Brazilian", "British", "Chinese", "Colombian",
  "Egyptian", "English", "Filipino", "French", "German", "Indian", "Indonesian", "Iranian", "Irish", "Italian",
  "Japanese", "Kenyan", "Korean", "Latino", "Malaysian", "Mexican", "Nepali", "Nigerian", "Pakistani", "Persian",
  "Russian", "Spanish", "Sri Lankan", "Thai", "Turkish", "Vietnamese", "Hanoi", "Saigon", "Beijing", "Shanghai",
  "Delhi", "Mumbai", "Manila", "Jakarta", "Lagos", "Nairobi", "Kathmandu", "Dhaka", "Karachi", "Bangkok",
].map((w) => w.toLowerCase());

export const norm = (a) => String(a || "").trim().replace(/\s+/g, " ");
const key = (a) => norm(a).toLowerCase();

export function isTaken(db, alias, exceptUserId = null) {
  const k = key(alias);
  return db.users.some((u) => u.id !== exceptUserId && u.alias && key(u.alias) === k);
}

// Random "Colour Animal". If all of them are taken, add a number.
export function suggestAlias(db) {
  for (let i = 0; i < 40; i++) {
    const a = `${COLOURS[Math.floor(Math.random() * COLOURS.length)]} ${ANIMALS[Math.floor(Math.random() * ANIMALS.length)]}`;
    if (!isTaken(db, a)) return a;
  }
  let n = 2;
  const base = `${COLOURS[0]} ${ANIMALS[0]}`;
  while (isTaken(db, `${base} ${n}`)) n++;
  return `${base} ${n}`;
}

/**
 * Check the format and the content of an alias. Returns an error message, or "" if the alias is good.
 * @param {string} alias
 * @param {string} realName  the user's name, so that the alias does not contain it
 */
export function aliasProblem(alias, realName = "") {
  const a = norm(alias);
  if (a.length < 3 || a.length > 30) return "Use 3 to 30 characters.";
  if (!/^[A-Za-z][A-Za-z '-]*[A-Za-z]$/.test(a)) return "Use letters, spaces, hyphens and apostrophes only.";
  const words = a.toLowerCase().split(/[\s'-]+/);
  const nameParts = String(realName).toLowerCase().split(/\s+/).filter((p) => p.length >= 3);
  if (nameParts.some((p) => words.includes(p))) return "Do not use your real name. Employers must not know who you are.";
  const lower = ` ${words.join(" ")} `;
  if (ORIGIN_WORDS.some((w) => lower.includes(` ${w} `))) return "Do not use a country, nationality or city. Use a neutral alias.";
  return "";
}
