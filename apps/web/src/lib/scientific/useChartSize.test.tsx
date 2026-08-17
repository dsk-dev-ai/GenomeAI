import { act, cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DEFAULT_CHART_WIDTH } from './geometry'
import { useChartSize } from './useChartSize'

function Probe({ height, fallbackWidth }: { height: number; fallbackWidth?: number }) {
  const size = useChartSize(height, fallbackWidth)
  return (
    <>
      <div ref={size.ref} data-testid="width">
        {size.width}
      </div>
      <div data-testid="height">{size.height}</div>
    </>
  )
}

class FakeResizeObserver {
  static instances: FakeResizeObserver[] = []
  callback: ResizeObserverCallback
  observed: Element[] = []
  disconnected = false

  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
    FakeResizeObserver.instances.push(this)
  }

  observe(target: Element) {
    this.observed.push(target)
  }

  unobserve() {}

  disconnect() {
    this.disconnected = true
  }
}

const realResizeObserver = globalThis.ResizeObserver

afterEach(() => {
  cleanup()
  globalThis.ResizeObserver = realResizeObserver
  FakeResizeObserver.instances = []
  vi.restoreAllMocks()
})

describe('useChartSize', () => {
  it('uses the default fallback width and fixed height before measurement', () => {
    render(<Probe height={400} />)
    expect(screen.getByTestId('width').textContent).toBe(String(DEFAULT_CHART_WIDTH))
    expect(screen.getByTestId('height').textContent).toBe('400')
  })

  it('honours a custom fallback width', () => {
    render(<Probe height={400} fallbackWidth={640} />)
    expect(screen.getByTestId('width').textContent).toBe('640')
  })

  it('measures the container width once when ResizeObserver is unavailable', () => {
    Object.defineProperty(globalThis, 'ResizeObserver', { value: undefined, configurable: true })
    const clientWidth = vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(777)

    render(<Probe height={400} />)
    expect(screen.getByTestId('width').textContent).toBe('777')
    clientWidth.mockRestore()
  })

  it('observes the element and updates on a resize when ResizeObserver exists', () => {
    globalThis.ResizeObserver = FakeResizeObserver as unknown as typeof ResizeObserver
    const clientWidth = vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get')

    clientWidth.mockReturnValue(500)
    render(<Probe height={400} />)
    expect(screen.getByTestId('width').textContent).toBe('500')
    expect(FakeResizeObserver.instances).toHaveLength(1)
    expect(FakeResizeObserver.instances[0].observed.length).toBe(1)

    clientWidth.mockReturnValue(900)
    act(() => {
      FakeResizeObserver.instances[0].callback([], FakeResizeObserver.instances[0])
    })
    expect(screen.getByTestId('width').textContent).toBe('900')

    clientWidth.mockRestore()
  })

  it('never overwrites the fallback width with a zero measurement', () => {
    globalThis.ResizeObserver = FakeResizeObserver as unknown as typeof ResizeObserver
    const clientWidth = vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(0)

    render(<Probe height={400} />)
    expect(screen.getByTestId('width').textContent).toBe(String(DEFAULT_CHART_WIDTH))

    clientWidth.mockRestore()
  })

  it('disconnects the observer on unmount', () => {
    globalThis.ResizeObserver = FakeResizeObserver as unknown as typeof ResizeObserver
    vi.spyOn(HTMLElement.prototype, 'clientWidth', 'get').mockReturnValue(500)

    const { unmount } = render(<Probe height={400} />)
    expect(FakeResizeObserver.instances[0].disconnected).toBe(false)
    unmount()
    expect(FakeResizeObserver.instances[0].disconnected).toBe(true)
  })
})
