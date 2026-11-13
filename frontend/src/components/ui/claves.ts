/**
 * Evaluación de contraseñas para el medidor (UiPasswordStrength). Guía, no autoridad:
 * el servidor decide (validadores de Django). Mínimo 10 caracteres (docs/ux/fase-2 §10, D14).
 */
export type NivelClave = 0 | 1 | 2 | 3

export interface RequisitoClave {
  id: 'longitud' | 'comun' | 'numerica' | 'parecida'
  texto: string
  cumple: boolean
}

export interface EvaluacionClave {
  /** Segmentos a llenar (0 si está vacía, 1–4 en otro caso). */
  segmentos: 0 | 1 | 2 | 3 | 4
  nivel: NivelClave | null
  etiqueta: string
  requisitos: RequisitoClave[]
  cumpleTodos: boolean
}

export const ETIQUETAS_NIVEL = ['Muy débil', 'Débil', 'Aceptable', 'Segura'] as const

/** Muestra acotada de contraseñas comunes (el servidor aplica la lista completa de Django). */
const COMUNES = new Set([
  'password', 'password1', 'password123', '123456', '1234567', '12345678', '123456789', '1234567890', '0123456789',
  'qwerty', 'qwerty123', 'qwertyuiop', 'abc123', 'abcd1234', 'iloveyou', 'admin', 'admin123', 'administrador',
  'letmein', 'welcome', 'monkey', 'dragon', 'master', 'login', 'passw0rd', 'contrasena', 'contrasena1',
  'contrasena123', 'contraseña', 'colombia', 'colombia123', 'meta1234', 'villavicencio', 'llanos123',
  'optiagro', 'optiagro123', 'optiagrollanos', 'universidad', 'unillanos', 'unillanos123', 'bienvenido',
  'bogota123', 'santafe', 'nacional', 'futbol', 'football', 'princess', 'sunshine', 'shadow', '1q2w3e4r', 'asdfghjkl',
  'zxcvbnm', '1qaz2wsx', 'qazwsx', '111111', '000000', '121212', 'q1w2e3r4',
])

function normalizar(texto: string): string {
  return texto
    .toLowerCase()
    .normalize('NFD')
    .replace(/[̀-ͯ]/g, '')
}

function esComun(clave: string): boolean {
  const n = normalizar(clave)
  if (COMUNES.has(n)) return true
  // Secuencias o repeticiones triviales: aaaaaaaaaa, 1111111111, abcdefghij, 0123456789
  if (/^(.)\1+$/.test(n)) return true
  if (n.length >= 6 && '0123456789012345678909876543210'.includes(n)) return true
  if (n.length >= 6 && 'abcdefghijklmnopqrstuvwxyz'.includes(n)) return true
  return false
}

function seParece(clave: string, referencias: string[]): boolean {
  const n = normalizar(clave)
  for (const ref of referencias) {
    const r = normalizar(ref).split('@')[0] ?? ''
    if (r.length >= 3 && (n.includes(r) || (n.length >= 4 && r.includes(n)))) return true
  }
  return false
}

export function evaluarClave(
  clave: string,
  contexto: { usuario?: string; correo?: string; minimo?: number } = {},
): EvaluacionClave {
  const minimo = contexto.minimo ?? 10
  const referencias = [contexto.usuario ?? '', contexto.correo ?? ''].filter((r) => r.trim() !== '')
  const requisitos: RequisitoClave[] = [
    { id: 'longitud', texto: `Al menos ${minimo} caracteres`, cumple: clave.length >= minimo },
    { id: 'comun', texto: 'No es una contraseña común', cumple: clave.length > 0 && !esComun(clave) },
    { id: 'numerica', texto: 'No es solo numérica', cumple: clave.length > 0 && !/^\d+$/.test(clave) },
    { id: 'parecida', texto: 'No se parece al usuario o correo', cumple: clave.length > 0 && !seParece(clave, referencias) },
  ]
  const cumpleTodos = requisitos.every((r) => r.cumple)

  if (clave.length === 0) {
    return { segmentos: 0, nivel: null, etiqueta: 'Escribe una contraseña', requisitos, cumpleTodos: false }
  }

  const clases = [/[a-z]/, /[A-Z]/, /\d/, /[^A-Za-z0-9]/].filter((re) => re.test(clave)).length
  let nivel: NivelClave
  if (!cumpleTodos) {
    nivel = clave.length < 6 || !requisitos[1]!.cumple ? 0 : 1
  } else if (clases >= 3 && clave.length >= 14) {
    nivel = 3
  } else {
    nivel = 2
  }
  return {
    segmentos: (nivel + 1) as 1 | 2 | 3 | 4,
    nivel,
    etiqueta: ETIQUETAS_NIVEL[nivel],
    requisitos,
    cumpleTodos,
  }
}
