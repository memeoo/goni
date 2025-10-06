import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { authAPI, setAuthToken, clearAuthToken } from '@/lib/api'
import { User, LoginFormData, RegisterFormData } from '@/types'
import toast from 'react-hot-toast'
import { useRouter } from 'next/navigation'

export function useAuth() {
  return useQuery({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const response = await authAPI.getMe()
      return response.data as User
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation({
    mutationFn: async (data: LoginFormData) => {
      const response = await authAPI.login(data.username, data.password)
      return response.data
    },
    onSuccess: (data) => {
      setAuthToken(data.access_token)
      queryClient.invalidateQueries({ queryKey: ['auth'] })
      toast.success('로그인에 성공했습니다')
      router.push('/dashboard')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || '로그인에 실패했습니다')
    },
  })
}

export function useRegister() {
  const router = useRouter()

  return useMutation({
    mutationFn: async (data: RegisterFormData) => {
      if (data.password !== data.confirmPassword) {
        throw new Error('비밀번호가 일치하지 않습니다')
      }
      
      const { confirmPassword, ...registerData } = data
      const response = await authAPI.register(registerData)
      return response.data
    },
    onSuccess: () => {
      toast.success('회원가입에 성공했습니다. 로그인해주세요.')
      router.push('/login')
    },
    onError: (error: any) => {
      if (error.message === '비밀번호가 일치하지 않습니다') {
        toast.error(error.message)
      } else {
        toast.error(error.response?.data?.detail || '회원가입에 실패했습니다')
      }
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  const router = useRouter()

  return useMutation({
    mutationFn: async () => {
      clearAuthToken()
      queryClient.clear()
    },
    onSuccess: () => {
      toast.success('로그아웃되었습니다')
      router.push('/')
    },
  })
}