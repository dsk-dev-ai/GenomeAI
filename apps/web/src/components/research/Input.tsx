interface InputProps {
  label: string
  placeholder: string
  value: string
  onChange: (value: string) => void
}

export function Input({ label, placeholder, value, onChange }: InputProps) {
  return (
    <label className="flex flex-col gap-1">
      <span className="text-xs font-medium text-gray-700">{label}</span>
      <input
        type="text"
        value={value}
        placeholder={placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      />
    </label>
  )
}
