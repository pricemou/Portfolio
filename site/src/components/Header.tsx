import Link from "next/link";
import { ThemeToggle } from "./ThemeToggle";

type Props = {
  lang: "fr" | "en";
  nav: Record<string, string>;
};

export function Header({ lang, nav }: Props) {
  const other = lang === "fr" ? "en" : "fr";
  const prefix = `/${lang}`;
  const links = [
    ["about", nav.about],
    ["experience", nav.experience],
    ["projects", nav.projects],
    ["skills", nav.skills],
    ["education", nav.education],
    ["contact", nav.contact],
  ] as const;

  return (
    <header className="sticky top-0 z-40 border-b border-line bg-bg/90 backdrop-blur">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3">
        <Link href={prefix} className="font-serif text-lg font-semibold text-ink">
          PFC
        </Link>
        <nav className="flex flex-wrap items-center gap-3 text-sm text-muted" aria-label="Main">
          {links.map(([id, label]) => (
            <a key={id} href={`${prefix}#${id}`} className="hover:text-accent">
              {label}
            </a>
          ))}
          <Link href={`/${other}`} className="font-medium text-ink hover:text-accent">
            {other.toUpperCase()}
          </Link>
          <a
            href={`/cv/cv-pricemou-${lang}.html`}
            className="rounded-md bg-accent px-3 py-1.5 font-medium text-white"
            target="_blank"
            rel="noopener noreferrer"
          >
            {nav.downloadCv}
          </a>
          <ThemeToggle label={nav.theme} />
        </nav>
      </div>
    </header>
  );
}
