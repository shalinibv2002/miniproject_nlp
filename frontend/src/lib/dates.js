// Date plumbing for the validator editors.
//
// A native `<input type="date">` speaks exactly one dialect: a full ISO
// calendar date (`YYYY-MM-DD`), or an empty string. That is the value the admin
// picks, and it is also the form `activity_date` is stored in, so ISO has to
// survive every parse/format round trip untouched -- anything that fails to
// recognise it silently blanks the input and the picked date is lost on the
// next render.
//
// Reported values are not always ISO, though: a derived report cell is free
// text ("12 Jan 2026 - 20 Jan 2026"), so the human forms are understood too.
// Anything that is not a real calendar date resolves to "" rather than a
// malformed value the browser would silently reject.

const MONTHS = {
  jan: "01", feb: "02", mar: "03", apr: "04", may: "05", jun: "06",
  jul: "07", aug: "08", sep: "09", oct: "10", nov: "11", dec: "12",
};

const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/;

// Day, month name, year. The gap between the day and the month is restricted to
// punctuation and whitespace: a wider "any non-digit" gap also matches letters
// and so clips a long month name ("12 January 2026" read as "nuary"), which is
// the form the report itself writes dates in.
const HUMAN_DATE = /(\d{1,2})[\s,./-]*([A-Za-z]{3,9})\.?[\s,]*(\d{4})/;

//: An en/em dash, "to"/"till", or a spaced hyphen. A bare hyphen is NOT a
//: separator because it is part of an ISO date, so it only counts when spaced.
const RANGE_SEPARATOR = /\s+-\s+|\s*(?:–|—|\bto\b|\btill\b)\s*/i;

// The month and day are re-checked against the calendar because Date.UTC rolls
// over silently (month 13 becomes the next January), which would hand the input
// a value the browser then rejects and blanks.
function calendarDate(year, month, day) {
  const stamp = new Date(Date.UTC(year, month - 1, day));
  if (stamp.getUTCFullYear() !== year
    || stamp.getUTCMonth() + 1 !== month
    || stamp.getUTCDate() !== day) {
    return "";
  }
  return `${year}-${String(month).padStart(2, "0")}-${String(day).padStart(2, "0")}`;
}

/** "12 Jan 2026" / "2026-01-12" -> "2026-01-12"; "" when not a real date. */
export function isoDate(value) {
  const text = value == null ? "" : String(value).trim();
  if (!text) return "";

  const iso = text.match(ISO_DATE);
  if (iso) {
    return calendarDate(Number(iso[1]), Number(iso[2]), Number(iso[3]));
  }

  const match = text.match(HUMAN_DATE);
  if (!match) return "";
  const month = MONTHS[match[2].slice(0, 3).toLowerCase()];
  if (!month) return "";
  return calendarDate(Number(match[3]), Number(month), Number(match[1]));
}

/**
 * Split a reported From-To value into the two ISO dates the inputs show.
 * "2026-01-12 - 2026-01-20" and "12 Jan 2026 - 20 Jan 2026" both give
 * ["2026-01-12", "2026-01-20"]. A lone date is the From end, matching how the
 * report itself reads a range; an unparseable end comes back "" so the admin
 * sees an empty box instead of a rejected value.
 */
export function splitDateRange(value) {
  const text = value == null ? "" : String(value).trim();
  if (!text) return ["", ""];
  const parts = text.split(RANGE_SEPARATOR).filter(Boolean);
  if (parts.length < 2) return [isoDate(text), ""];
  return [isoDate(parts[0]), isoDate(parts[parts.length - 1])];
}

/**
 * Join the two ISO dates back into the single value the record's report column
 * holds. `splitDateRange(joinDateRange(a, b))` is always `[a, b]`, so what the
 * admin sees before saving is what the reopened record shows afterwards.
 */
export function joinDateRange(from, to) {
  const left = String(from == null ? "" : from).trim();
  const right = String(to == null ? "" : to).trim();
  if (left && right) return `${left} – ${right}`;
  return left || right || "";
}