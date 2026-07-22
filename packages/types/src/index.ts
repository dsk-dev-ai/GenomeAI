export type Environment = 'development' | 'staging' | 'production'

export interface HealthResponse {
  status: 'ok' | 'error'
}

export interface VersionInfo {
  version: string
  name: string
}
