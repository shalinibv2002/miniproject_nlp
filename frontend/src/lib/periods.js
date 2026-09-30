export const BEFORE_2021 = "Before 2021";

export const PERIOD_LABELS = {
  "2021-22": "2021-2022",
  "2022-23": "2022-2023",
  "2023-24": "2023-2024",
  "2024-25": "2024-2025",
  "2025-26": "2025-2026",
};

export const PUBLIC_PERIODS = Object.keys(PERIOD_LABELS);

/** Periods shown in charts and filters: the five public years plus the
 *  historical bucket. */
export const ALL_PERIODS = [...PUBLIC_PERIODS, BEFORE_2021];

export function periodLabel(period) {
  return PERIOD_LABELS[period] || BEFORE_2021;
}