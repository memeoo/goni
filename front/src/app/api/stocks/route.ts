import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET() {
  try {
    console.log(`[API Proxy] Fetching from: ${BACKEND_URL}/api/stocks/`)

    const response = await fetch(`${BACKEND_URL}/api/stocks/`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    console.log(`[API Proxy] Backend response status: ${response.status}`)

    const data = await response.json()

    // 백엔드가 500 에러를 반환해도 데이터는 전달
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch stocks data', details: String(error) },
      { status: 500 }
    )
  }
}
