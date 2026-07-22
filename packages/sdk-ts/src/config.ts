export interface SDKConfig {
  baseUrl: string
  apiKey?: string
  timeout: number
}

export const defaultConfig: SDKConfig = {
  baseUrl: 'http://localhost:8000',
  timeout: 30_000,
}
