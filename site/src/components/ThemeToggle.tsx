"use client";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

export function ThemeToggle({ label }: { label: string }) {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  if (!mounted) return null;
  const next = theme === "dark" ? "light" : "dark";
  return (
    <button
      type="button"
      aria-label={label}
      className="rounded-md border border-line px-2 py-1 text-sm text-muted hover:text-ink"
      onClick={() => setTheme(next)}
    >
      {theme === "dark" ? "Light" : "Dark"}
    </button>
  );
}
