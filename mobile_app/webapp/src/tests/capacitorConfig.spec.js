import { readFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

function readCapacitorConfig() {
  const url = new URL('../../capacitor.config.json', import.meta.url)
  return JSON.parse(readFileSync(url, 'utf8'))
}

describe('Capacitor config contract', () => {
  it('declares app identity and web asset directory', () => {
    const config = readCapacitorConfig()
    expect(config.appId).toBe('ch.spotonsight.mobile')
    expect(config.appName).toBe('SpotOnSight')
    expect(config.webDir).toBe('dist')
  })

  it('keeps native plugin defaults required by mobile shell', () => {
    const config = readCapacitorConfig()
    expect(config.plugins?.Keyboard?.resize).toBe('body')
    expect(config.plugins?.SplashScreen?.launchAutoHide).toBe(true)
  })
})
