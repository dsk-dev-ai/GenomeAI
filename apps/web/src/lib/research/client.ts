export const API_BASE_URL = process.env.NEXT_PUBLIC_GENOMEAI_API_URL ?? 'http://localhost:8000'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      ...init?.headers,
    },
  })

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => (body as { detail?: string }).detail ?? response.statusText)
      .catch(() => response.statusText)
    throw new Error(detail)
  }

  return (await response.json()) as T
}

export function post<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

export async function get<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'GET' })
}
