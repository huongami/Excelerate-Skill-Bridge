// Shared lists for levels, skill levels, work modes, page sizes and the compare basket (Jinder V2 plan, sections 4 and 7).
// Other files import these. Do not write the same lists again.

/** Job and talent levels, from the lowest (rank 0) to the highest (rank 5). */
export const LEVELS = ["Intern", "Junior", "Mid", "Senior", "Lead", "Principal"];

/** Skill levels 1 to 5. `value` is the number that the API uses. */
export const SKILL_LEVELS = [
  { value: 1, label: "Beginner" },
  { value: 2, label: "Working" },
  { value: 3, label: "Proficient" },
  { value: 4, label: "Advanced" },
  { value: 5, label: "Expert" },
];

/** How the work is done. `location` of a job stays a city or "Remote". */
export const WORK_MODES = ["Onsite", "Hybrid", "Remote"];

/** The numbers of rows that a list can show on one page. The first one is the default. */
export const PAGE_SIZES = [10, 20, 50];

/** The most items in one compare basket (one basket for each kind). */
export const COMPARE_MAX = 5;

/** The rank of a level name (0 to 5), or -1 if the name is not a level. */
export const levelRank = (name) => LEVELS.indexOf(name);

/** The label of a skill level number (1 to 5), or "" if there is none. Also takes "3" or 3.0. */
export function skillLevelLabel(value) {
  const n = Math.round(Number(value));
  const found = SKILL_LEVELS.find((s) => s.value === n);
  return found ? found.label : "";
}
