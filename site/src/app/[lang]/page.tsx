import { notFound } from "next/navigation";
import { HomePage } from "@/components/HomePage";
import { getContent, Lang } from "@/lib/content";

export function generateStaticParams() {
  return [{ lang: "fr" }, { lang: "en" }];
}

export default function LangHome({ params }: { params: { lang: string } }) {
  if (params.lang !== "fr" && params.lang !== "en") notFound();
  const lang = params.lang as Lang;
  return <HomePage lang={lang} content={getContent(lang)} />;
}
