/**
 * Three.js Molecular Structure viewer (Phase 6.12).
 *
 * The WebGL implementation behind the `MolecularViewer` contract. It owns the
 * scene graph, camera, orbit controls, lights, resize handling, animation
 * loop, and — critically — full resource disposal. The React layer never
 * touches Three.js directly; it creates one viewer per mounted component and
 * drives it through the `MolecularViewer` methods.
 *
 * WebGL is isolated to `createRenderer` so tests can inject a fake renderer
 * and exercise the full lifecycle (frame, focus, representation, dispose)
 * without a GPU.
 */

import * as THREE from 'three'
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js'

import type { Point3 } from '@/lib/molecular/geometry'
import type { RepresentationId } from '@/lib/molecular/representations'
import type { MolecularStructure } from '@/lib/molecular/types'

import { buildStructureGroup, disposeGroup } from './representationBuilder'
import type { CreateThreeViewerOptions, MolecularViewer, ThreeRenderer } from './types'

/** Camera-to-structure distance as a multiple of the structure radius. */
const CAMERA_DISTANCE_FACTOR = 3
/** Minimum camera distance in angstroms (tiny structures). */
const MIN_CAMERA_DISTANCE = 2
/** Default view direction used when the camera has no prior orientation. */
const DEFAULT_VIEW_DIRECTION = new THREE.Vector3(1, 1, 1).normalize()

function defaultRenderer(): ThreeRenderer {
  return new THREE.WebGLRenderer({ antialias: true, alpha: true })
}

/**
 * Creates a Three.js molecular viewer attached to `container`. The renderer
 * factory is injectable so unit tests can supply a fake WebGL-free renderer.
 */
export function createThreeViewer(
  container: HTMLElement,
  options: CreateThreeViewerOptions = {},
): MolecularViewer {
  const renderer = options.createRenderer ? options.createRenderer() : defaultRenderer()
  renderer.setPixelRatio(typeof window !== 'undefined' ? window.devicePixelRatio : 1)
  renderer.setClearColor(0xffffff, 0)
  renderer.domElement.style.width = '100%'
  renderer.domElement.style.height = '100%'
  renderer.domElement.style.display = 'block'
  container.appendChild(renderer.domElement)

  const scene = new THREE.Scene()
  const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 10_000)
  camera.position.set(
    DEFAULT_VIEW_DIRECTION.x * 10,
    DEFAULT_VIEW_DIRECTION.y * 10,
    DEFAULT_VIEW_DIRECTION.z * 10,
  )

  const controls = new OrbitControls(camera, renderer.domElement)
  controls.enableDamping = true
  controls.dampingFactor = 0.1

  scene.add(new THREE.AmbientLight(0xffffff, 0.7))
  const keyLight = new THREE.DirectionalLight(0xffffff, 0.9)
  keyLight.position.set(2, 2, 2)
  scene.add(keyLight)
  const fillLight = new THREE.DirectionalLight(0xffffff, 0.4)
  fillLight.position.set(-2, -1, 1)
  scene.add(fillLight)

  const structureGroup = new THREE.Group()
  scene.add(structureGroup)

  let disposed = false
  let currentStructure: MolecularStructure | undefined
  let currentRepresentation: RepresentationId | undefined
  let groupVisible = true

  function renderFrame(): void {
    controls.update()
    renderer.render(scene, camera)
  }

  function applySize(): void {
    const width = Math.max(container.clientWidth || 1, 1)
    const height = Math.max(container.clientHeight || 1, 1)
    camera.aspect = width / height
    camera.updateProjectionMatrix()
    renderer.setSize(width, height)
  }

  applySize()
  renderer.setAnimationLoop(() => renderFrame())

  let resizeObserver: ResizeObserver | null = null
  if (typeof ResizeObserver !== 'undefined') {
    resizeObserver = new ResizeObserver(() => applySize())
    resizeObserver.observe(container)
  }

  function rebuild(): void {
    if (currentStructure === undefined || currentRepresentation === undefined) return
    disposeGroup(structureGroup)
    structureGroup.clear()
    structureGroup.visible = groupVisible
    structureGroup.add(buildStructureGroup(currentStructure, currentRepresentation))
  }

  return {
    setStructure(structure, representation) {
      currentStructure = structure
      currentRepresentation = representation
      rebuild()
    },
    setRepresentation(representation) {
      currentRepresentation = representation
      rebuild()
    },
    setVisible(visible) {
      groupVisible = visible
      structureGroup.visible = visible
    },
    focusCamera(target: Point3, radius: number) {
      const center = new THREE.Vector3(target.x, target.y, target.z)
      const distance = Math.max(radius * CAMERA_DISTANCE_FACTOR, MIN_CAMERA_DISTANCE)

      const offset = new THREE.Vector3().subVectors(camera.position, controls.target)
      const direction = offset.lengthSq() > 0 ? offset.normalize() : DEFAULT_VIEW_DIRECTION

      camera.position.copy(center).addScaledVector(direction, distance)
      camera.near = Math.max(radius / 100, 0.001)
      camera.far = Math.max(radius * 50, 100)
      camera.updateProjectionMatrix()
      camera.lookAt(center)
      controls.target.copy(center)
      controls.update()
    },
    resize(width, height) {
      camera.aspect = width / height
      camera.updateProjectionMatrix()
      renderer.setSize(Math.max(width, 1), Math.max(height, 1))
    },
    dispose() {
      if (disposed) return
      disposed = true
      resizeObserver?.disconnect()
      resizeObserver = null
      renderer.setAnimationLoop(null)
      controls.dispose()
      disposeGroup(structureGroup)
      structureGroup.clear()
      renderer.dispose()
      if (renderer.domElement.parentNode === container) {
        container.removeChild(renderer.domElement)
      }
    },
  }
}
