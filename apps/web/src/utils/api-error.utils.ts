import { apiErrorBodySchema } from "@/interfaces/api.interface";

/** Pydantic prefixes messages raised by validators; the text after it is the legacy message. */
const VALUE_ERROR_PREFIX = /^Value error, /;

/** What a non-OK API response says: the safe message, the error code and the feature data. */
export interface ApiErrorBody {
  message: string;
  code: string | null;
  data: unknown;
}

/**
 * Read a non-OK API response. A 422 validation error carries the useful text in its first field
 * (e.g. "Policy names must be unique."); otherwise the API's public `message`, else the status.
 */
export async function readErrorBody(response: Response): Promise<ApiErrorBody> {
  const fallback = `Request failed (${response.status})`;
  try {
    const body = apiErrorBodySchema.parse(await response.json());
    const data = body.data ?? null;
    if (typeof body.error === "string") {
      return { message: body.message || body.error, code: body.error, data };
    }
    const code = body.error?.code ?? null;
    const field = body.error?.fields?.[0];
    if (field) {
      return {
        message: field.message.replace(VALUE_ERROR_PREFIX, ""),
        code,
        data,
      };
    }
    return { message: body.message || fallback, code, data };
  } catch {
    return { message: fallback, code: null, data: null };
  }
}

/** Message of a non-OK API response (see `readErrorBody`). */
export async function readErrorMessage(response: Response): Promise<string> {
  return (await readErrorBody(response)).message;
}
