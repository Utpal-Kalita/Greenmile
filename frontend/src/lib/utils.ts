export function cn(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

export function formatSeconds(value: number) {
  return `${value.toFixed(value < 10 ? 2 : 1)}s`;
}

export function formatPercent(value: number) {
  return `${value.toFixed(1)}%`;
}
