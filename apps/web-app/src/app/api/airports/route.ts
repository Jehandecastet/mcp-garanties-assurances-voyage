// instantair-app/src/app/api/airports/route.ts
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url)
  const query = searchParams.get('search') || ''

  console.log(`API autocomplete airports called with query: ${query}`)

  // TODO: Call your instantair-proxy or an external API here
  // For now return an empty list or mock data
  const results: Array<{ code: string; name: string }> = []

  return NextResponse.json(results)
}
