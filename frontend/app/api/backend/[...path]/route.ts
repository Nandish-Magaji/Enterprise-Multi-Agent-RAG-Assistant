import { getAccessToken } from "@logto/next/server-actions";
import { logtoConfig } from "@/app/logto";

const backendUrl = process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";
const apiResource = process.env.LOGTO_API_RESOURCE;

async function proxy(request: Request, context: { params: Promise<{ path: string[] }> }) {
  if (!apiResource) return Response.json({ detail: "LOGTO_API_RESOURCE is not configured." }, { status: 503 });

  let accessToken: string;
  try {
    accessToken = await getAccessToken(logtoConfig, apiResource);
  } catch {
    return Response.json({ detail: "Authentication is required." }, { status: 401 });
  }

  const { path } = await context.params;
  const incomingUrl = new URL(request.url);
  const targetUrl = new URL(`${backendUrl}/${path.join("/")}`);
  targetUrl.search = incomingUrl.search;
  const headers = new Headers(request.headers);
  headers.set("Authorization", `Bearer ${accessToken}`);
  headers.delete("host");

  return fetch(targetUrl, {
    method: request.method,
    headers,
    body: ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer(),
    redirect: "manual",
  });
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
