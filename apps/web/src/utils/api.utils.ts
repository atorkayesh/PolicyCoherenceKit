import type { z } from "zod";
import { API_V1_PREFIX } from "@/constants/api.constants";
import env from "@/env";
import type { StepError } from "@/interfaces/project.interface";
import { readErrorBody } from "@/utils/api-error.utils";
import { filenameFromDisposition } from "@/utils/content-disposition.utils";

/** Build a full API v1 URL, e.g. `/health` → `http://localhost:50002/api/v1/health`. */
export function buildApiUrl(
  path: string,
  baseUrl: string = env.VITE_API_BASE_URL,
): string {
  return `${baseUrl}${API_V1_PREFIX}${path}`;
}

/**
 * A non-OK API response. `message` is the API's public message (safe to show), `code` its stable
 * error code and `data` the feature error's payload (for example `{title, field}`).
 */
export class ApiError extends Error {
  readonly status: number;
  readonly code: string | null;
  readonly data: unknown;

  constructor(
    message: string,
    status: number,
    code: string | null = null,
    data: unknown = null,
  ) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.code = code;
    this.data = data;
  }
}

/** Call the API: `path` is below `/api/v1` and may carry a query string. No cookies: the API is public. */
export function apiFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  return fetch(buildApiUrl(path), init);
}

/** `init` for a JSON POST body. */
export function jsonPost(body: unknown): RequestInit {
  return {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  };
}

/** Throw `ApiError` with the API's message, code and data when the response is not OK. */
export async function ensureOk(response: Response): Promise<Response> {
  if (!response.ok) {
    const body = await readErrorBody(response);
    throw new ApiError(body.message, response.status, body.code, body.data);
  }
  return response;
}

/**
 * Call a JSON endpoint and return its validated `data`.
 *
 * `schema` is the `apiResponseSchema(...)` of the endpoint; a missing `data` is an error.
 */
export async function apiData<T>(
  path: string,
  init: RequestInit,
  schema: z.ZodType<{ data?: T | null }>,
): Promise<T> {
  const response = await ensureOk(await apiFetch(path, init));
  const body = schema.parse(await response.json());
  if (body.data == null) {
    throw new ApiError("The API response has no data", response.status);
  }
  return body.data;
}

/** Call a binary endpoint and return the file. */
export async function apiBlob(path: string, init: RequestInit): Promise<Blob> {
  const response = await ensureOk(await apiFetch(path, init));
  return response.blob();
}

/** A downloaded file with the name the API gave it in `Content-Disposition` (else `fallback`). */
export async function apiFile(
  path: string,
  init: RequestInit,
  fallback: string,
): Promise<{ blob: Blob; filename: string }> {
  const response = await ensureOk(await apiFetch(path, init));
  const filename = filenameFromDisposition(
    response.headers.get("Content-Disposition"),
    fallback,
  );
  return { blob: await response.blob(), filename };
}

/** Message of any error for display: the API's message, or the error's own. */
export function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : String(error);
}

/** The legacy message-box title the API sent with an error (`data.title`), if any. */
export function errorTitle(error: unknown): string | null {
  if (!(error instanceof ApiError)) return null;
  const data = error.data as { title?: unknown } | null;
  return data && typeof data.title === "string" ? data.title : null;
}

/** The API error code of an error, if any. */
export function errorCode(error: unknown): string | null {
  return error instanceof ApiError ? error.code : null;
}

/** An error as shown under a question: message, legacy title, optional action. */
export function stepError(
  error: unknown,
  action?: StepError["action"],
): StepError {
  return { message: errorMessage(error), title: errorTitle(error), action };
}
