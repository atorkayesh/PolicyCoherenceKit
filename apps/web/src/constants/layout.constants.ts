export const APP_NAME = "Policy Coherence Kit";

/** The legacy slogan (app.py:469), reserved for the future About page. */
export const APP_SUBTITLE =
  "Evaluate interactions between policies using multiple decision-makers";

/** The app name for the footer credit. */
export const APP_FULL_NAME = "Policy Coherence Kit";

/** Institutional credits shown between the app name and year. */
export const FOOTER_LINKS: readonly { label: string; href: string }[] = [
  { label: "Forschungszentrum Jülich", href: "https://www.fz-juelich.de/en" },
];

export const PAGE_TITLES = {
  HOME: "Policy Coherence Kit",
  STATUS: "Status · Policy Coherence Kit",
} as const;

export const NOT_FOUND_TEXT = {
  TITLE: "Page not found",
  BODY: "This page does not exist.",
  LINK: "Go to the assessment",
} as const;
