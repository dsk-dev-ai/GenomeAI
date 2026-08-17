import * as THREE from 'three'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { MolecularStructure } from '../types'
import { createThreeViewer } from './threeViewer'
import type { ThreeRenderer } from './types'

interface FakeRendererHarness {
  renderer: ThreeRenderer & {
    setPixelRatio: ReturnType<typeof vi.fn>
    setSize: ReturnType<typeof vi.fn>
    setClearColor: ReturnType<typeof vi.fn>
    dispose: ReturnType<typeof vi.fn>
  }
  loop: ((time: number) => void) | null
  lastScene: unknown
  lastCamera: unknown
  setAnimationLoopCalls: Array<((time: number) => void) | null>
}

function createFakeRenderer(): FakeRendererHarness {
  const harness: FakeRendererHarness = {
    renderer: {
      domElement: document.createElement('canvas'),
      setPixelRatio: vi.fn(),
      setSize: vi.fn(),
      setClearColor: vi.fn(),
      setAnimationLoop: vi.fn(),
      render: vi.fn(),
      dispose: vi.fn(),
    },
    loop: null,
    lastScene: undefined,
    lastCamera: undefined,
    setAnimationLoopCalls: [],
  }
  const renderer = harness.renderer
  renderer.setAnimationLoop = vi.fn((callback: ((time: number) => void) | null) => {
    harness.setAnimationLoopCalls.push(callback)
    harness.loop = callback
  })
  renderer.render = vi.fn((scene: unknown, camera: unknown) => {
    harness.lastScene = scene
    harness.lastCamera = camera
  })
  return harness
}

class MockResizeObserver implements ResizeObserver {
  callback: ResizeObserverCallback
  observed = new Set<Element>()
  constructor(callback: ResizeObserverCallback) {
    this.callback = callback
  }
  observe(target: Element) {
    this.observed.add(target)
  }
  unobserve(target: Element) {
    this.observed.delete(target)
  }
  disconnect() {
    this.observed.clear()
  }
}

function structure(): MolecularStructure {
  return {
    id: 'viewer',
    chains: [
      {
        id: 'A',
        residues: [
          { index: 1, atomIndices: [1] },
          { index: 2, atomIndices: [2] },
        ],
      },
    ],
    atoms: [
      { index: 1, element: 'C', x: 0, y: 0, z: 0, residueIndex: 1, chainId: 'A', atomName: 'CA' },
      { index: 2, element: 'N', x: 4, y: 0, z: 0, residueIndex: 2, chainId: 'A', atomName: 'CA' },
    ],
    bonds: [],
  }
}

let previousResizeObserver: typeof ResizeObserver | undefined

afterEach(() => {
  if (previousResizeObserver === undefined) {
    ;(globalThis as Record<string, unknown>).ResizeObserver = undefined
  } else {
    globalThis.ResizeObserver = previousResizeObserver
  }
  previousResizeObserver = undefined
  vi.restoreAllMocks()
})

describe('createThreeViewer', () => {
  it('appends the canvas and renders frames through the animation loop', () => {
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })

    expect(container.contains(fake.renderer.domElement)).toBe(true)
    viewer.setStructure(structure(), 'cartoon')
    fake.loop?.(0)

    expect(fake.renderer.render).toHaveBeenCalledTimes(1)
    expect(fake.lastCamera).toBeInstanceOf(THREE.PerspectiveCamera)
    expect(fake.lastScene).toBeInstanceOf(THREE.Scene)
  })

  it('frames the camera around a target with a distance proportional to the radius', () => {
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })

    fake.loop?.(0)
    const camera = fake.lastCamera as THREE.PerspectiveCamera

    viewer.focusCamera({ x: 0, y: 0, z: 0 }, 5)
    expect(camera.position.length()).toBeCloseTo(15)
    expect(camera.near).toBeCloseTo(0.05)
    expect(camera.far).toBe(250)

    viewer.focusCamera({ x: 10, y: 0, z: 0 }, 1)
    const position = camera.position
    const distance = new THREE.Vector3(position.x - 10, position.y, position.z).length()
    expect(distance).toBeCloseTo(Math.max(1 * 3, 2))
  })

  it('handles an explicit resize', () => {
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })
    viewer.resize(400, 300)
    expect(fake.renderer.setSize).toHaveBeenCalledWith(400, 300)
  })

  it('observes the container size when ResizeObserver is available', () => {
    previousResizeObserver = globalThis.ResizeObserver
    globalThis.ResizeObserver = MockResizeObserver
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })
    viewer.setStructure(structure(), 'ball-and-stick')
    expect(globalThis.ResizeObserver).toBe(MockResizeObserver)
    viewer.dispose()
  })

  it('disposes the renderer, stops the loop, and detaches the canvas', () => {
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })
    viewer.setStructure(structure(), 'space-filling')

    viewer.dispose()
    expect(fake.renderer.dispose).toHaveBeenCalledTimes(1)
    expect(fake.setAnimationLoopCalls.at(-1)).toBeNull()
    expect(fake.renderer.domElement.parentNode).toBeNull()
  })

  it('keeps the render loop healthy across representation and visibility changes', () => {
    const fake = createFakeRenderer()
    const container = document.createElement('div')
    const viewer = createThreeViewer(container, { createRenderer: () => fake.renderer })
    viewer.setStructure(structure(), 'cartoon')
    viewer.setRepresentation('ball-and-stick')
    viewer.setVisible(false)
    viewer.setVisible(true)

    fake.loop?.(0)
    fake.loop?.(0)
    expect(fake.renderer.render).toHaveBeenCalledTimes(2)
  })
})
