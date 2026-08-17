import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { GenomicInterval } from '@/lib/genome/types'
import type { WorkspaceDataSource } from '@/lib/workspace/dataSources'

import { ResearchWorkspace } from './ResearchWorkspace'
import { fixtureWorkspaceDataSource } from './fixtureDataSources'

const TP53_WINDOW = { chromosome: 'chr17', start: 7_650_000, end: 7_700_000 }
const BRCA1_REGION = { chromosome: 'chr17', start: 43_044_295, end: 43_125_483 }

const PANEL_TITLES = [
  'Genome Browser',
  'Gene / Transcript Viewer',
  'Biological Network Viewer',
  'Protein Viewer',
  'Expression Chart',
  'Expression Heatmap',
  'Volcano Plot',
  'Coverage Chart',
  'Distribution Chart',
]

function lastInterval(loader: ReturnType<typeof vi.fn>): GenomicInterval {
  const calls = loader.mock.calls
  return calls[calls.length - 1][0] as GenomicInterval
}

function dataSourceWithSpies(overrides: Partial<WorkspaceDataSource> = {}) {
  const loadGenomeGenes = vi.fn(fixtureWorkspaceDataSource.loadGenomeGenes)
  const loadGenomeVariants = vi.fn(fixtureWorkspaceDataSource.loadGenomeVariants)
  const dataSource: WorkspaceDataSource = {
    ...fixtureWorkspaceDataSource,
    ...overrides,
    loadGenomeGenes,
    loadGenomeVariants,
  }
  return { dataSource, loadGenomeGenes, loadGenomeVariants }
}

afterEach(() => {
  cleanup()
})

describe('ResearchWorkspace', () => {
  it('renders the context selector and every panel heading', async () => {
    render(<ResearchWorkspace dataSource={fixtureWorkspaceDataSource} />)

    expect(screen.getByRole('combobox', { name: 'Research context' })).toBeInTheDocument()
    expect(screen.getByRole('textbox', { name: 'Go to region' })).toBeInTheDocument()

    await waitFor(() => {
      for (const title of PANEL_TITLES) {
        expect(screen.getByRole('heading', { name: title })).toBeInTheDocument()
      }
    })
  })

  it('drives the genome browser tracks with the shared context region', async () => {
    const { dataSource, loadGenomeGenes } = dataSourceWithSpies()
    render(<ResearchWorkspace dataSource={dataSource} />)

    await waitFor(() => expect(loadGenomeGenes).toHaveBeenCalled())
    expect(lastInterval(loadGenomeGenes)).toEqual(TP53_WINDOW)

    fireEvent.change(screen.getByRole('combobox', { name: 'Research context' }), {
      target: { value: 'brca1-locus' },
    })

    await waitFor(() => expect(lastInterval(loadGenomeGenes)).toEqual(BRCA1_REGION))
    expect(screen.getByTestId('active-context')).toHaveTextContent('BRCA1 locus (chr17)')
  })

  it('syncs the gene / transcript viewer to the same context region', async () => {
    render(<ResearchWorkspace dataSource={fixtureWorkspaceDataSource} />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: 'Gene / Transcript Viewer' })).toBeInTheDocument()
    })

    fireEvent.change(screen.getByRole('combobox', { name: 'Research context' }), {
      target: { value: 'brca1-locus' },
    })

    await waitFor(() =>
      expect(screen.getByTestId('active-context')).toHaveTextContent('BRCA1 locus (chr17)'),
    )
    expect(screen.getAllByText('BRCA1', { exact: true }).length).toBeGreaterThan(0)
  })

  it('loads a custom region and drives the browser to it', async () => {
    const { dataSource, loadGenomeGenes } = dataSourceWithSpies()
    render(<ResearchWorkspace dataSource={dataSource} />)
    await waitFor(() => expect(loadGenomeGenes).toHaveBeenCalled())

    const form = screen.getByRole('form', { name: 'Load custom region' })
    fireEvent.change(within(form).getByRole('textbox', { name: 'Go to region' }), {
      target: { value: 'chr1:100-200' },
    })
    fireEvent.click(within(form).getByRole('button', { name: 'Go' }))

    await waitFor(() =>
      expect(lastInterval(loadGenomeGenes)).toEqual({ chromosome: 'chr1', start: 100, end: 200 }),
    )
    expect(screen.getByTestId('active-context')).toHaveTextContent('chr1:100-200')
  })

  it('shows an empty state when the context region has no gene structure', async () => {
    const dataSource: WorkspaceDataSource = {
      ...fixtureWorkspaceDataSource,
      loadGenes: () => Promise.resolve([]),
    }
    render(<ResearchWorkspace dataSource={dataSource} />)

    await waitFor(() =>
      expect(screen.getByText('No gene structure to show in this region.')).toBeInTheDocument(),
    )
  })

  it('shows an error state with a retry control when a panel loader fails', async () => {
    const dataSource: WorkspaceDataSource = {
      ...fixtureWorkspaceDataSource,
      loadNetwork: () => Promise.reject(new Error('Network unavailable')),
    }
    render(<ResearchWorkspace dataSource={dataSource} />)

    await waitFor(() => expect(screen.getByRole('alert')).toHaveTextContent('Network unavailable'))
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
  })

  it('shows a loading state while a panel loader is pending', () => {
    const dataSource: WorkspaceDataSource = {
      ...fixtureWorkspaceDataSource,
      loadGenes: () => new Promise(() => undefined),
    }
    render(<ResearchWorkspace dataSource={dataSource} />)

    expect(
      screen
        .getAllByRole('status')
        .some((node) => node.textContent?.includes('Loading gene structure...')),
    ).toBe(true)
  })

  it('keeps whole-dataset panels independent when the context region changes', async () => {
    const loadNetwork = vi.fn(fixtureWorkspaceDataSource.loadNetwork)
    const loadProtein = vi.fn(fixtureWorkspaceDataSource.loadProtein)
    const dataSource: WorkspaceDataSource = {
      ...fixtureWorkspaceDataSource,
      loadNetwork,
      loadProtein,
    }
    render(<ResearchWorkspace dataSource={dataSource} />)

    await waitFor(() => expect(loadNetwork).toHaveBeenCalledTimes(1))
    await waitFor(() => expect(loadProtein).toHaveBeenCalledTimes(1))

    fireEvent.change(screen.getByRole('combobox', { name: 'Research context' }), {
      target: { value: 'brca1-locus' },
    })
    await waitFor(() =>
      expect(screen.getByTestId('active-context')).toHaveTextContent('BRCA1 locus (chr17)'),
    )

    expect(loadNetwork).toHaveBeenCalledTimes(1)
    expect(loadProtein).toHaveBeenCalledTimes(1)
  })
})
