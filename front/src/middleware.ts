import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const token = request.cookies.get('access_token')?.value
  const { pathname } = request.nextUrl

  // 공개 경로 (로그인, 회원가입)
  const publicPaths = ['/login', '/register']
  const isPublicPath = publicPaths.some(path => pathname.startsWith(path))

  // 보호된 경로 (대시보드, 프로필 등)
  const protectedPaths = ['/dashboard', '/profile']
  const isProtectedPath = protectedPaths.some(path => pathname.startsWith(path))

  // 루트 경로 처리는 별도로 처리 (middleware에서 처리하지 않음)
  if (pathname === '/') {
    return NextResponse.next()
  }

  // 로그인된 사용자가 공개 페이지에 접근하려는 경우 대시보드로 리디렉션
  if (token && isPublicPath) {
    return NextResponse.redirect(new URL('/dashboard', request.url))
  }

  // 로그인되지 않은 사용자가 보호된 페이지에 접근하려는 경우 로그인 페이지로 리디렉션
  if (!token && isProtectedPath) {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}
