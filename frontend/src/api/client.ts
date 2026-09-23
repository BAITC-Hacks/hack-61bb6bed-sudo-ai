export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
  ) {
    super(message);
  }
}
export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const csrf = document.cookie
    .split("; ")
    .find((v) => v.startsWith("sana_csrf="))
    ?.split("=")[1];
  let response: Response;
  try {
    response = await fetch("/api/v1" + path, {
      ...init,
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        ...(csrf ? { "X-CSRF-Token": decodeURIComponent(csrf) } : {}),
        ...init.headers,
      },
    });
  } catch {
    throw new Error(
      "Не удалось связаться с сервером. Проверьте подключение и повторите попытку.",
    );
  }
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401 && !path.startsWith("/auth/login"))
      window.dispatchEvent(new Event("sana:unauthorized"));
    const detail = data.error?.details
      ?.map((e: { message: string }) => e.message)
      .join(" ");
    throw new ApiError(
      response.status,
      data.error?.code || "error",
      detail || data.error?.message || "Не удалось выполнить запрос.",
    );
  }
  return data;
}
export const post = <T>(path: string, data?: unknown) =>
  api<T>(path, {
    method: "POST",
    body: data === undefined ? undefined : JSON.stringify(data),
  });
export const patch = <T>(path: string, data: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(data) });
