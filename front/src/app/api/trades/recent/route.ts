import { NextResponse } from 'next/server'

const BACKEND_URL = process.env.BACKEND_URL || 'http://localhost:8000'

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const days = searchParams.get('days') || '10'

    console.log(`[API Proxy] Fetching recent trades from: ${BACKEND_URL}/api/trading-plans/trades/recent?days=${days}`)

    const response = await fetch(`${BACKEND_URL}/api/trading-plans/trades/recent?days=${days}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    })

    console.log(`[API Proxy] Backend response status: ${response.status}`)

    const data = await response.json()

    // 백엔드 응답 그대로 전달
    return NextResponse.json(data, { status: response.status })
  } catch (error) {
    console.error('[API Proxy] Error:', error)
    return NextResponse.json(
      { error: 'Failed to fetch recent trades', details: String(error) },
      { status: 500 }
    )
  }
}
