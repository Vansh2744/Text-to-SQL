export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  if (n < 1024 ** 2) return `${(n / 1024).toFixed(1)} KB`;
  return `${(n / 1024 ** 2).toFixed(1)} MB`;
}

export function formatCell(v: unknown): string {
  if (v === null || v === undefined) return "null";
  if (typeof v === "number")
    return Number.isInteger(v)
      ? v.toLocaleString()
      : v.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(v);
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export function toCsv(columns: string[], rows: unknown[][]): string {
  const cell = (v: unknown) => {
    if (v === null || v === undefined) return "";
    let s = String(v);
    if (/^[=+\-@]/.test(s) && typeof v === "string") s = `'${s}`;
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
  };
  return [
    columns.map(cell).join(","),
    ...rows.map((r) => r.map(cell).join(",")),
  ].join("\n");
}

export function isNumericType(t: string): boolean {
  return /^(TINYINT|SMALLINT|INTEGER|BIGINT|HUGEINT|UTINYINT|USMALLINT|UINTEGER|UBIGINT|FLOAT|DOUBLE|DECIMAL)/i.test(
    t,
  );
}

export function suggestQuestions(
  columns: { name: string; type: string }[],
): string[] {
  const num = columns.find((c) => isNumericType(c.type));
  const cat = columns.find((c) => /VARCHAR/i.test(c.type));
  const date = columns.find((c) => /^(DATE|TIMESTAMP)/i.test(c.type));
  const out = ["How many rows are in this dataset?"];
  if (num && cat) out.push(`What is the total ${num.name} by ${cat.name}?`);
  if (num && cat) out.push(`Top 5 ${cat.name} by ${num.name}`);
  if (num && date) out.push(`Show ${num.name} by month`);
  if (num) out.push(`What is the average ${num.name}?`);
  return out;
}
