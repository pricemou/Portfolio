"""Génère le fichier events.csv (50 000 événements simulés)."""
from __future__ import annotations

from .data_engine import default_events_path, generate_events_dataframe, save_events_csv


def main() -> None:
    path = default_events_path()
    print(f'Generation de 50 000 evenements -> {path}')
    df = generate_events_dataframe(n_events=50_000, days=30, seed=42)
    save_events_csv(df, path)
    print(f'OK - {len(df)} lignes ecrites.')


if __name__ == '__main__':
    main()
