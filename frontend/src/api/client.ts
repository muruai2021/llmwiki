// Generic JSON fetch wrapper with:
//   - error normalization (ApiError)
//   - module-level in-flight dedup (so 225 wikilinks firing resolveWikilink
//     for the same target result in 1 network call, not 225)
//   - module-level response cache (TTL 5 min for GET)
//   - concurrency limiter (max 8 in flight)

export class ApiError extends Error {
  status: number;
  code: string;
  details: Record<string, unknown>;

  constructor(status: number, code: string, message: string, details: Record<string, unknown> = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.message = message;
    this.details = details;
  }
}

export interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "DELETE";
  query?: Record<string, string | number | boolean | undefined>;
  body?: unknown;
  signal?: AbortSignal;
}

const CACHE_TTL_MS = 5 * 60 * 1000;
const MAX_CONCURRENCY = 8;

interface CacheEntry {
  expires: number;
  promise: Promise<unknown>;
}

const cache = new Map<string, CacheEntry>();
const inflight = new Map<string, Promise<unknown>>();

function makeKey(path: string, opts: RequestOptions): string {
  const { method = "GET", query, body } = opts;
  return `${method} ${path}?${new URLSearchParams(
    Object.entries(query || {}).map(([k, v]) => [k, v == null ? "" : String(v)]),
  ).toString()}#${body !== undefined ? JSON.stringify(body) : ""}`;
}

let active = 0;
const waiters: Array<() => void> = [];

async function acquire(): Promise<void> {
  if (active < MAX_CONCURRENCY) {
    active++;
    return;
  }
  await new Promise<void>((resolve) => waiters.push(resolve));
  active++;
}

function release(): void {
  active--;
  const next = waiters.shift();
  if (next) next();
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const { method = "GET", query, body, signal } = opts;
  const key = makeKey(path, opts);

  // Cache + inflight dedup
  if (method === "GET") {
    const cached = cache.get(key);
    if (cached && cached.expires > Date.now()) {
      return (await cached.promise) as T;
    }
    const inFlight = inflight.get(key);
    if (inFlight) {
      return (await inFlight) as T;
    }
  }

  const url = new URL(path, window.location.origin);
  if (query) {
    for (const [k, v] of Object.entries(query)) {
      if (v !== undefined && v !== null) {
        url.searchParams.set(k, String(v));
      }
    }
  }
  const headers: Record<string, string> = {};
  let payload: BodyInit | undefined;
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }

  const work = (async () => {
    await acquire();
    try {
      const res = await fetch(url.toString(), { method, headers, body: payload, signal });
      const ct = res.headers.get("content-type") || "";
      if (!res.ok) {
        let errPayload: any = null;
        if (ct.includes("application/json")) {
          try { errPayload = await res.json(); } catch {}
        }
        const code = errPayload?.error?.code || `http_${res.status}`;
        const message = errPayload?.error?.message || res.statusText;
        const details = errPayload?.error?.details || {};
        throw new ApiError(res.status, code, message, details);
      }
      if (ct.includes("application/json")) {
        return (await res.json()) as unknown;
      }
      return (await res.text()) as unknown;
    } finally {
      release();
    }
  })();

  if (method === "GET") {
    cache.set(key, { expires: Date.now() + CACHE_TTL_MS, promise: work });
    inflight.set(key, work);
    work.finally(() => {
      inflight.delete(key);
    });
  }

  try {
    return (await work) as T;
  } catch (e) {
    if (method === "GET") cache.delete(key);
    throw e;
  }
}

/** Drop all cached GET responses. Used after writes so stale reads don't linger. */
export function invalidateCache(): void {
  cache.clear();
}

/** Test-only: number of cached GET entries. Returns 0 in production code
 *  paths because no one calls this from app code; exists so unit tests can
 *  assert that a write-through cleared the cache. */
export function _cacheSizeForTest(): number {
  return cache.size;
}
