/** Decode a JWT payload without verifying the signature (already verified by the API). */
export function decodeJwt(token: string): Record<string, string> | null {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const raw = JSON.parse(
      decodeURIComponent(
        atob(base64)
          .split('')
          .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
          .join(''),
      ),
    )
    // Normaliza claim types — .NET usa URIs longas para claims conhecidas.
    return {
      sub: raw.sub,
      email: raw.email,
      nome: raw.nome,
      role: raw['http://schemas.microsoft.com/ws/2008/06/identity/claims/role'] || raw.role,
      escritorio_id: raw.escritorio_id,
      deve_trocar_senha: raw.deve_trocar_senha,
      exp: raw.exp,
    }
  } catch {
    return null
  }
}

/** True se o token não puder ser decodificado ou já tiver expirado. */
export function isJwtExpired(token: string): boolean {
  const payload = decodeJwt(token)
  const exp = payload?.exp ? Number(payload.exp) : NaN
  if (!Number.isFinite(exp)) return true
  return Date.now() >= exp * 1000
}
