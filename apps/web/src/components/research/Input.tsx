interface InputProps {
  label: string
  placeholder: string
  value: string
  onChange: (value: string) => void
  helper?: string
}

export function Input({ label, placeholder, value, onChange, helper }: InputProps) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">{label}</span>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-2.5 text-sm text-slate-900 shadow-sm transition-all placeholder:text-slate-400 focus:border-genome-500 focus:outline-none focus:ring-4 focus:ring-genome-500/10"
      />
      {helper ? <span className="text-xs text-slate-400">{helper}</span> : null}
    </label>
  )
}
