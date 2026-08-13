'use client'

import { ExpressionChart } from '@/components/scientific/ExpressionChart'
import { TP53_PATHWAY_EXPRESSION_FIXTURE } from '@/lib/scientific/expression.fixtures'
import { useExpressionChart } from '@/lib/scientific/useExpressionChart'

/**
 * Client-side demonstration of the Phase 6.7 Scientific Charts.
 *
 * Loads a deterministic development fixture (see
 * `lib/scientific/expression.fixtures.ts`) through the same data lifecycle as
 * a production dataset. The loader flips to `fetchExpressionDataset` once the
 * backend exposes an expression endpoint.
 */
export function ScientificDemo() {
  const result = useExpressionChart({
    loader: (signal) => {
      if (signal.aborted) return Promise.reject(new DOMException('Aborted', 'AbortError'))
      return Promise.resolve(TP53_PATHWAY_EXPRESSION_FIXTURE)
    },
  })

  return <ExpressionChart result={result} title="Expression Chart" />
}
