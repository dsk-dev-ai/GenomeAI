'use client'

export default function ErrorPage({
  error,
  reset,
}: {
  error: Error & { digest?: string }
  reset: () => void
}) {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-8">
      <h1 className="text-2xl font-semibold text-red-600">Something went wrong</h1>
      <p className="mt-2 text-gray-600">{error.message}</p>
      <button
        onClick={() => reset()}
        className="mt-6 rounded-md bg-gray-900 px-4 py-2 text-sm font-medium text-white hover:bg-gray-700"
        type="button"
      >
        Try again
      </button>
    </main>
  )
}
