'use client'

import { AnalyzeButton } from './AnalyzeButton'
import { Input } from './Input'
import { Reveal } from './Reveal'

export interface FieldConfig {
  key: string
  label: string
  placeholder: string
  value: string
  onChange: (value: string) => void
  helper?: string
}

export function AnalysisForm({
  fields,
  onSubmit,
  loading,
  disabled,
  submitLabel,
}: {
  fields: FieldConfig[]
  onSubmit: () => void
  loading: boolean
  disabled: boolean
  submitLabel?: string
}) {
  return (
    <Reveal variant="down">
      <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-card">
        <div className="flex flex-wrap items-end gap-4">
          {fields.map((f) => (
            <div key={f.key} className="min-w-[200px] flex-1">
              <Input
                label={f.label}
                placeholder={f.placeholder}
                value={f.value}
                onChange={f.onChange}
                helper={f.helper}
              />
            </div>
          ))}
          <AnalyzeButton onClick={onSubmit} loading={loading} disabled={disabled}>
            {submitLabel}
          </AnalyzeButton>
        </div>
      </div>
    </Reveal>
  )
}
