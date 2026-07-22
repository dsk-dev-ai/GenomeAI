import type { SDKConfig } from './config'
import { defaultConfig } from './config'
import { VERSION } from './version'

export class GenomeAIClient {
  public readonly config: SDKConfig
  public readonly version: string = VERSION

  constructor(config?: Partial<SDKConfig>) {
    this.config = { ...defaultConfig, ...config } as SDKConfig
  }
}
