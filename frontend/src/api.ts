export async function api<T>(path: string, body: unknown): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(`/api/${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    let data;
    try {
      data = await response.json();
    } catch {
      throw new Error(
        "The backend returned an invalid response. Check that it is running on port 8000.",
      );
    }
    if (!response.ok) {
      const detail = data?.detail;
      const message =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail
                .map(
                  (item: { loc?: unknown[]; msg?: string }) =>
                    `${item.loc?.slice(1).join(".") || "Request"}: ${item.msg || "Invalid value"}`,
                )
                .join("; ")
            : "Unable to complete this request.";
      throw new Error(message);
    }
    return data;
  } catch (error) {
    if (controller.signal.aborted)
      throw new Error(
        "The request timed out. Check the backend connection and try again.",
      );
    if (error instanceof TypeError)
      throw new Error(
        "Cannot reach the backend. Check that it is running and try again.",
      );
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
