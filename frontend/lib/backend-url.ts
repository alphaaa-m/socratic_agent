export function backendUrl(path: string): string {
  const base = (process.env.BACKEND_API_URL ?? "http://localhost:8000/api/v1").replace(/\/+$/, "");
  return `${base}/${path.replace(/^\/+/, "")}`;
}
