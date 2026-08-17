import type * as THREE from 'three'
import { describe, expect, it, vi } from 'vitest'

import type { MolecularStructure } from '../types'
import { buildStructureGroup, disposeGroup } from './representationBuilder'

function structure(): MolecularStructure {
  return {
    id: 'builder',
    chains: [
      {
        id: 'A',
        residues: [
          { index: 1, atomIndices: [1, 2] },
          { index: 2, atomIndices: [3, 4] },
        ],
      },
    ],
    atoms: [
      { index: 1, element: 'C', x: 0, y: 0, z: 0, residueIndex: 1, chainId: 'A', atomName: 'CA' },
      {
        index: 2,
        element: 'N',
        x: 0.5,
        y: 0.4,
        z: -0.6,
        residueIndex: 1,
        chainId: 'A',
        atomName: 'N',
      },
      { index: 3, element: 'C', x: 4, y: 0, z: 0, residueIndex: 2, chainId: 'A', atomName: 'CA' },
      {
        index: 4,
        element: 'O',
        x: 4.4,
        y: -0.6,
        z: 0.5,
        residueIndex: 2,
        chainId: 'A',
        atomName: 'O',
      },
    ],
    bonds: [
      { atomA: 1, atomB: 2 },
      { atomA: 2, atomB: 3 },
      { atomA: 3, atomB: 4 },
    ],
  }
}

function countMeshes(group: THREE.Group): number {
  let count = 0
  group.traverse((object) => {
    if ((object as THREE.Mesh).isMesh) count += 1
  })
  return count
}

describe('buildStructureGroup', () => {
  it('builds one sphere per atom for ball-and-stick', () => {
    const group = buildStructureGroup(structure(), 'ball-and-stick')
    expect(countMeshes(group)).toBe(4 + 3)
  })

  it('builds spheres only for space-filling (no bonds)', () => {
    const group = buildStructureGroup(structure(), 'space-filling')
    expect(countMeshes(group)).toBe(4)
  })

  it('builds a cartoon ribbon tube per chain backbone', () => {
    const group = buildStructureGroup(structure(), 'cartoon')
    const ribbons = group.children.filter(
      (child) => (child as THREE.Mesh).isMesh && child.name.startsWith('cartoon-'),
    )
    expect(ribbons).toHaveLength(1)
  })

  it('returns an empty group for a structure without atoms', () => {
    const empty: MolecularStructure = { id: 'empty', chains: [], atoms: [], bonds: [] }
    expect(buildStructureGroup(empty, 'ball-and-stick').children).toHaveLength(0)
    expect(buildStructureGroup(empty, 'cartoon').children).toHaveLength(0)
  })
})

describe('disposeGroup', () => {
  it('disposes every geometry and material owned by the group', () => {
    const group = buildStructureGroup(structure(), 'ball-and-stick')
    const disposeCalls: string[] = []
    group.traverse((object) => {
      const mesh = object as THREE.Mesh
      if (mesh.isMesh) {
        const geometry = mesh.geometry
        const material = mesh.material as THREE.Material
        vi.spyOn(geometry, 'dispose').mockImplementation(() => {
          disposeCalls.push('geometry')
        })
        vi.spyOn(material, 'dispose').mockImplementation(() => {
          disposeCalls.push('material')
        })
      }
    })

    disposeGroup(group)
    expect(disposeCalls.filter((entry) => entry === 'geometry')).toHaveLength(7)
    expect(disposeCalls.filter((entry) => entry === 'material')).toHaveLength(7)
  })
})
