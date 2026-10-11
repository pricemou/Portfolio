import Link from "next/link";
import { notFound } from "next/navigation";
import { Header } from "@/components/Header";
import { getContent, getProject, Lang } from "@/lib/content";

export function generateStaticParams() {
  const fr = getContent("fr");
  return ["fr", "en"].flatMap((lang) =>
    fr.projects.map((p) => ({ lang, slug: p.slug }))
  );
}

export default function ProjectPage({
  params,
}: {
  params: { lang: string; slug: string };
}) {
  if (params.lang !== "fr" && params.lang !== "en") notFound();
  const lang = params.lang as Lang;
  const content = getContent(lang);
  const project = getProject(lang, params.slug);
  if (!project) notFound();
  const ui = content.ui as any;

  return (
    <>
      <Header lang={lang} nav={content.nav} />
      <main className="mx-auto max-w-3xl px-4 py-12">
        <Link href={`/${lang}#projects`} className="text-sm text-accent hover:underline">
          ← {content.nav.projects}
        </Link>
        <h1 className="mt-4 font-serif text-4xl text-ink">{project.title}</h1>
        <p className="mt-3 text-lg text-muted">{project.glance}</p>

        <Section title={ui.context} text={project.context} />
        <Section title={ui.data} text={project.data} />
        <ListSection title={ui.approach} items={project.approach} />
        <ListSection title={ui.methods} items={project.methods} />
        <ListSection title={ui.deliverables} items={project.deliverables} />
        <ListSection title={ui.demonstrates} items={project.demonstrates} />
        <ListSection title={ui.improvements} items={project.improvements} />

        <h2 className="mt-8 font-serif text-2xl text-ink">{ui.technologies}</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {project.technologies.map((t: string) => (
            <span key={t} className="rounded-full border border-line px-2 py-0.5 text-xs text-muted">{t}</span>
          ))}
        </div>
        <a href={project.github} target="_blank" rel="noopener noreferrer" className="mt-6 inline-block text-accent hover:underline">
          {ui.github}
        </a>
      </main>
    </>
  );
}

function Section({ title, text }: { title: string; text: string }) {
  return (
    <section className="mt-8">
      <h2 className="font-serif text-2xl text-ink">{title}</h2>
      <p className="mt-2 text-muted">{text}</p>
    </section>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="mt-8">
      <h2 className="font-serif text-2xl text-ink">{title}</h2>
      <ul className="mt-2 list-disc space-y-2 pl-5 text-muted">
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}
