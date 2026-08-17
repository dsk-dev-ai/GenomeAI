/**
 * Structure representation builder (Phase 6.12).
 *
 * Builds the Three.js object graph for one representation of a structure.
 * This module only creates Three.js **objects** (geometries, materials,
 * meshes, curves) — it never touches WebGL — so it is fully unit-testable in
 * jsdom. Rendering and lifecycle live in `threeViewer.ts`.
 *
 * Representation extensions: add a branch in `buildStructureGroup` and a
 * catalog entry in `lib/molecular/representations.ts`.
 */

import * as THREE from 'three'

import { backboneTrace, elementPresentation } from '@/lib/molecular/geometry'
import type { Point3 } from '@/lib/molecular/geometry'
import type { RepresentationId } from '@/lib/molecular/representations'
import type { MolecularStructure, StructureAtom } from '@/lib/molecular/types'

/** Colour used by the cartoon ribbon. */
const CARTOON_COLOR = 0x4f7cc0
/** Radius of the cartoon ribbon tube, in angstroms. */
const CARTOON_TUBE_RADIUS = 0.6
/** Cylinder radius for ball-and-stick bonds, in angstroms. */
const BOND_RADIUS = 0.14

function atomMesh(atom: StructureAtom, radius: number): THREE.Mesh {
  const presentation = elementPresentation(atom.element)
  const geometry = new THREE.SphereGeometry(radius, 16, 12)
  const material = new THREE.MeshStandardMaterial({ color: `#${presentation.color}` })
  const mesh = new THREE.Mesh(geometry, material)
  mesh.position.set(atom.x, atom.y, atom.z)
  return mesh
}

/**
 * A cylinder between two points, oriented along the bond axis. Returns a
 * mesh whose disposal must be tracked alongside its geometry/material.
 */
function bondCylinder(a: Point3, b: Point3, radius: number): THREE.Mesh {
  const start = new THREE.Vector3(a.x, a.y, a.z)
  const end = new THREE.Vector3(b.x, b.y, b.z)
  const direction = new THREE.Vector3().subVectors(end, start)
  const length = direction.length()
  const geometry = new THREE.CylinderGeometry(radius, radius, length, 8, 1)
  const material = new THREE.MeshStandardMaterial({ color: 0xb0b0b0 })
  const mesh = new THREE.Mesh(geometry, material)
  const midpoint = new THREE.Vector3().addVectors(start, end).multiplyScalar(0.5)
  mesh.position.copy(midpoint)
  if (length > 0) {
    mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize())
  }
  return mesh
}

function buildBallAndStick(structure: MolecularStructure): THREE.Group {
  const group = new THREE.Group()
  const byIndex = new Map(structure.atoms.map((atom) => [atom.index, atom]))

  for (const atom of structure.atoms) {
    group.add(atomMesh(atom, elementPresentation(atom.element).ballRadius))
  }
  for (const bond of structure.bonds) {
    const atomA = byIndex.get(bond.atomA)
    const atomB = byIndex.get(bond.atomB)
    if (atomA === undefined || atomB === undefined) continue
    group.add(bondCylinder(atomA, atomB, BOND_RADIUS))
  }
  return group
}

function buildSpaceFilling(structure: MolecularStructure): THREE.Group {
  const group = new THREE.Group()
  for (const atom of structure.atoms) {
    group.add(atomMesh(atom, elementPresentation(atom.element).vanDerWaalsRadius))
  }
  return group
}

function buildCartoon(structure: MolecularStructure): THREE.Group {
  const group = new THREE.Group()
  const traces = backboneTrace(structure)
  for (const [chainId, points] of traces) {
    if (points.length < 2) continue
    const curve = new THREE.CatmullRomCurve3(
      points.map((point) => new THREE.Vector3(point.x, point.y, point.z)),
    )
    const geometry = new THREE.TubeGeometry(
      curve,
      Math.max(points.length * 4, 16),
      CARTOON_TUBE_RADIUS,
      8,
      false,
    )
    const material = new THREE.MeshStandardMaterial({ color: CARTOON_COLOR })
    const mesh = new THREE.Mesh(geometry, material)
    mesh.name = `cartoon-${chainId}`
    group.add(mesh)
  }
  return group
}

/**
 * Builds the object graph for a representation. Callers own the returned
 * group and must dispose its geometries/materials (see `disposeGroup`).
 */
export function buildStructureGroup(
  structure: MolecularStructure,
  representation: RepresentationId,
): THREE.Group {
  switch (representation) {
    case 'ball-and-stick':
      return buildBallAndStick(structure)
    case 'space-filling':
      return buildSpaceFilling(structure)
    case 'cartoon':
      return buildCartoon(structure)
  }
}

/** Disposes every geometry and material owned by a group (recursively). */
export function disposeGroup(group: THREE.Object3D): void {
  group.traverse((object) => {
    const mesh = object as THREE.Mesh
    if (mesh.isMesh) {
      mesh.geometry?.dispose()
      const material = mesh.material
      if (Array.isArray(material)) {
        for (const entry of material) entry.dispose()
      } else {
        material?.dispose()
      }
    }
  })
}
