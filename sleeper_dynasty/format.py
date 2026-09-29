"""Minimal table printer (no external deps)."""


def table(headers: list, rows: list):
    rows = [[("" if c is None else str(c)) for c in row] for row in rows]
    widths = [len(h) for h in headers]
    for row in rows:
        for i, c in enumerate(row):
            widths[i] = max(widths[i], len(c))

    def fmt_row(cols):
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cols))

    print(fmt_row(headers))
    print("  ".join("-" * w for w in widths))
    for row in rows:
        print(fmt_row(row))
