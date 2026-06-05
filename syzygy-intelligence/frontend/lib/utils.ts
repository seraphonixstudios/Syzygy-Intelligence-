import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(date: string | Date) {
  return new Intl.DateTimeFormat("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(date));
}

export function truncate(str: string, length: number = 100) {
  if (str.length <= length) return str;
  return str.slice(0, length) + "...";
}

export function polarityColor(polarity: string) {
  switch (polarity) {
    case "masculine":
      return "#d4a843";
    case "feminine":
      return "#8a7f7a";
    case "unified":
      return "#e8dcc8";
    default:
      return "#d4a843";
  }
}

export function polarityGlyph(polarity: string) {
  switch (polarity) {
    case "masculine":
      return "☉";
    case "feminine":
      return "☽";
    case "unified":
      return "☿";
    default:
      return "☿";
  }
}
