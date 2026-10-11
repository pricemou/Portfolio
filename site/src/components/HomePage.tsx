"use client";
import Image from "next/image";
import Link from "next/link";
import { useMemo, useState } from "react";
import { Header } from "./Header";

type Lang = "fr" | "en";

export function HomePage({ lang, content }: { lang: Lang; content: any }) {
  const { hero, about, experiences, projects, skills, education, certifications, ui, meta, nav } = content;
  const [filter, setFilter] = useState("all");
  const [showAllCerts, setShowAllCerts] = useState(false);
  const [certDomain, setCertDomain] = useState("all");

  const filteredProjects = useMemo(() => {
    if (filter === "all") return projects;
    return projects.filter((p: any) => p.category === filter);
  }, [filter, projects]);

  const featured = certifications.items.filter((c: any) => c.featured);
  const certList = showAllCerts
    ? certifications.items.filter((c: any) => certDomain === "all" || c.domain === certDomain)
    : featured;

  return (
    <>
      <Header lang={lang} nav={nav} />
      <main className="mx-auto max-w-6xl px-4 pb-20">
        <section className="grid items-center gap-10 py-14 md:grid-cols-2">
          <div>
            <p className="text-sm font-medium text-accent">{hero.location}</p>
            <h1 className="mt-2 font-serif text-4xl font-semibold tracking-tight text-ink md:text-5xl">
              {hero.name}
            </h1>
            <p className="mt-3 text-lg text-muted">{hero.title}</p>
            <p className="mt-4 max-w-prose text-base leading-relaxed text-ink">{hero.tagline}</p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a href="#experience" className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">{hero.ctaExperience}</a>
              <a href="#projects" className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink">{hero.ctaProjects}</a>
              <a href={`/cv/cv-pricemou-${lang}.html`} target="_blank" rel="noopener noreferrer" className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink">{hero.ctaCv}</a>
              <a href="#contact" className="rounded-md border border-line px-4 py-2 text-sm font-medium text-ink">{hero.ctaContact}</a>
            </div>
          </div>
          <div className="justify-self-center">
            <Image
              src="/images/claude-pricemou.png"
              alt={hero.photoAlt}
              width={420}
              height={520}
              className="rounded-lg border border-line object-cover shadow-sm"
              priority
            />
          </div>
        </section>

        <section id="about" className="scroll-mt-24 border-t border-line py-14">
          <p className="text-sm font-medium uppercase tracking-wide text-accent">{about.eyebrow}</p>
          <h2 className="mt-2 font-serif text-3xl text-ink">{about.lead}</h2>
          <div className="mt-4 max-w-prose space-y-3 text-muted">
            {about.body.map((p: string) => (
              <p key={p}>{p}</p>
            ))}
          </div>
          <div className="mt-8">
            <p className="mb-3 text-sm font-medium text-ink">{ui.pipelineTitle}</p>
            <ol className="flex flex-wrap gap-2">
              {ui.pipeline.map((step: string, i: number) => (
                <li key={step} className="rounded-full border border-line bg-surface px-3 py-1 text-sm text-muted">
                  {i + 1}. {step}
                </li>
              ))}
            </ol>
          </div>
        </section>

        <section id="experience" className="scroll-mt-24 border-t border-line py-14">
          <h2 className="font-serif text-3xl text-ink">{ui.sectionExperience}</h2>
          <div className="mt-8 space-y-6">
            {experiences.map((exp: any) => (
              <article key={exp.id} className="rounded-xl border border-line bg-surface p-6 shadow-sm">
                <header className="flex flex-wrap items-baseline justify-between gap-2">
                  <div>
                    <h3 className="font-serif text-2xl text-ink">{exp.role}</h3>
                    <p className="text-accent">{exp.org}</p>
                  </div>
                  <p className="text-sm text-muted">{exp.period}</p>
                </header>
                <p className="mt-3 font-medium text-ink">{exp.oneLiner}</p>
                <p className="mt-2 text-muted">{exp.context}</p>
                <div className="mt-5 grid gap-4 md:grid-cols-2">
                  <div className="rounded-lg border border-line p-4">
                    <p className="mb-2 inline-block rounded-full bg-accent/10 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-accent">{exp.soloLabel}</p>
                    <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                      {exp.solo.map((item: string) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                  <div className="rounded-lg border border-line p-4">
                    <p className="mb-2 inline-block rounded-full bg-ink/5 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-ink">{exp.collabLabel}</p>
                    <ul className="list-disc space-y-2 pl-5 text-sm text-muted">
                      {exp.collab.map((item: string) => <li key={item}>{item}</li>)}
                    </ul>
                  </div>
                </div>
                {exp.technologies?.length > 0 && (
                  <div className="mt-4 flex flex-wrap gap-2">
                    {exp.technologies.map((t: string) => (
                      <span key={t} className="rounded-full border border-line px-2 py-0.5 text-xs text-muted">{t}</span>
                    ))}
                  </div>
                )}
                <ul className="mt-4 list-disc pl-5 text-sm text-ink">
                  {exp.skillsShown.map((s: string) => <li key={s}>{s}</li>)}
                </ul>
              </article>
            ))}
          </div>
        </section>

        <section id="projects" className="scroll-mt-24 border-t border-line py-14">
          <h2 className="font-serif text-3xl text-ink">{ui.sectionProjects}</h2>
          <div className="mt-4 flex flex-wrap gap-2">
            {Object.entries(ui.filters).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setFilter(key)}
                className={`rounded-full px-3 py-1 text-sm ${filter === key ? "bg-accent text-white" : "border border-line text-muted"}`}
              >
                {label as string}
              </button>
            ))}
          </div>
          <div className="mt-8 grid gap-4 md:grid-cols-2">
            {filteredProjects.map((p: any) => (
              <article key={p.slug} className="flex flex-col rounded-xl border border-line bg-surface p-5">
                <p className="text-xs uppercase tracking-wide text-accent">{ui.filters[p.category]}</p>
                <h3 className="mt-1 font-serif text-xl text-ink">{p.title}</h3>
                <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-muted">
                  {p.cardLines.map((l: string) => <li key={l}>{l}</li>)}
                </ul>
                <p className="mt-3 text-sm font-medium text-ink">{ui.impact} : {p.impact}</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {p.technologies.map((t: string) => (
                    <span key={t} className="rounded-full border border-line px-2 py-0.5 text-xs text-muted">{t}</span>
                  ))}
                </div>
                <Link href={`/${lang}/projects/${p.slug}`} className="mt-4 text-sm font-medium text-accent hover:underline">
                  {ui.caseStudy}
                </Link>
              </article>
            ))}
          </div>
        </section>

        <section id="skills" className="scroll-mt-24 border-t border-line py-14">
          <h2 className="font-serif text-3xl text-ink">{ui.sectionSkills}</h2>
          <div className="mt-8 space-y-8">
            {skills.map((group: any) => (
              <div key={group.group}>
                <h3 className="font-serif text-xl text-ink">{group.group}</h3>
                <ul className="mt-3 grid gap-3 md:grid-cols-2">
                  {group.items.map((item: any) => (
                    <li key={item.name} className="rounded-lg border border-line bg-surface p-3">
                      <p className="font-medium text-ink">{item.name}</p>
                      <p className="mt-1 text-xs text-muted">{ui.proof} : {item.proof}</p>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </section>

        <section id="education" className="scroll-mt-24 border-t border-line py-14">
          <h2 className="font-serif text-3xl text-ink">{ui.sectionEducation}</h2>
          <ul className="mt-6 space-y-4">
            {education.map((ed: any) => (
              <li key={ed.title + ed.school} className="rounded-lg border border-line bg-surface p-4">
                <p className="font-medium text-ink">{ed.title}</p>
                <p className="text-muted">{ed.school}</p>
                {ed.period ? <p className="text-sm text-muted">{ed.period}</p> : null}
                {ed.note ? <p className="mt-1 text-sm text-muted">{ed.note}</p> : null}
              </li>
            ))}
          </ul>

          <h3 className="mt-10 font-serif text-2xl text-ink">{ui.featuredCerts}</h3>
          {!showAllCerts ? null : (
            <div className="mt-3 flex flex-wrap gap-2">
              <button type="button" onClick={() => setCertDomain("all")} className={`rounded-full px-3 py-1 text-sm ${certDomain === "all" ? "bg-accent text-white" : "border border-line text-muted"}`}>{ui.filters.all}</button>
              {Object.entries(certifications.domains).map(([key, labels]: any) => (
                <button key={key} type="button" onClick={() => setCertDomain(key)} className={`rounded-full px-3 py-1 text-sm ${certDomain === key ? "bg-accent text-white" : "border border-line text-muted"}`}>
                  {labels[lang]}
                </button>
              ))}
            </div>
          )}
          <ul className="mt-4 grid gap-3 md:grid-cols-2">
            {certList.map((c: any) => (
              <li key={c.code} className="rounded-lg border border-line bg-surface p-4">
                <p className="font-medium text-ink">{c.title}</p>
                <p className="mt-1 text-sm text-muted">{c.skill[lang]}</p>
                <a href={c.url} target="_blank" rel="noopener noreferrer" className="mt-2 inline-block text-sm text-accent hover:underline">
                  {ui.verify}
                </a>
              </li>
            ))}
          </ul>
          <button
            type="button"
            className="mt-4 text-sm font-medium text-accent hover:underline"
            onClick={() => setShowAllCerts((v) => !v)}
          >
            {showAllCerts ? ui.seeLess : ui.allCerts}
          </button>
        </section>

        <section id="contact" className="scroll-mt-24 border-t border-line py-14">
          <h2 className="font-serif text-3xl text-ink">{ui.sectionContact}</h2>
          <p className="mt-2 max-w-prose text-muted">{ui.contactLead}</p>
          <div className="mt-4 flex flex-wrap gap-4 text-sm">
            <a className="text-accent hover:underline" href={`mailto:${meta.email}`}>{meta.email}</a>
            <a className="text-accent hover:underline" href={meta.linkedin} target="_blank" rel="noopener noreferrer">LinkedIn</a>
            <a className="text-accent hover:underline" href={meta.github} target="_blank" rel="noopener noreferrer">GitHub</a>
          </div>
          <form className="mt-8 max-w-xl space-y-3" action={`mailto:${meta.email}`} method="post" encType="text/plain">
            <label className="block text-sm">
              <span className="text-muted">{ui.name}</span>
              <input name="name" required className="mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink" />
            </label>
            <label className="block text-sm">
              <span className="text-muted">{ui.email}</span>
              <input type="email" name="email" required className="mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink" />
            </label>
            <label className="block text-sm">
              <span className="text-muted">{ui.subject}</span>
              <input name="subject" required className="mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink" />
            </label>
            <label className="block text-sm">
              <span className="text-muted">{ui.message}</span>
              <textarea name="message" required rows={5} className="mt-1 w-full rounded-md border border-line bg-surface px-3 py-2 text-ink" />
            </label>
            <button type="submit" className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-white">{ui.send}</button>
          </form>
        </section>
      </main>
      <footer className="border-t border-line py-6 text-center text-sm text-muted">{ui.footer}</footer>
    </>
  );
}
