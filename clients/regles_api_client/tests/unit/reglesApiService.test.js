import { describe, it, expect, beforeEach, vi } from 'vitest'
import {
  listerRegles,
  annoterRegle,
  ErreurAuthentification,
} from '../../src/services/reglesApiService.js'
import { API_REGLES_URL } from '../../src/apiServer.js'

// apiServer.js est modifié à la main selon l'environnement (dev/prod) : les
// tests lisent sa valeur courante plutôt que de coder une URL en dur, sinon
// ils casseraient dès qu'on bascule apiServer.js sur une autre valeur.
const BASE_URL = API_REGLES_URL.replace(/\/+$/, '')

describe('listerRegles', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('appelle GET /regles et renvoie le JSON', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => [{ numero: 1 }],
    })

    const regles = await listerRegles()

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/regles`)
    expect(regles).toEqual([{ numero: 1 }])
  })

  it('lève une erreur si la réponse n\'est pas ok', async () => {
    fetch.mockResolvedValue({ ok: false, status: 500, json: async () => ({}) })

    await expect(listerRegles()).rejects.toThrow()
  })
})

describe('annoterRegle', () => {
  beforeEach(() => {
    vi.stubGlobal('fetch', vi.fn())
  })

  it('envoie un PATCH avec le header Authorization', async () => {
    fetch.mockResolvedValue({
      ok: true,
      status: 200,
      json: async () => ({ numero: 28, review_status: 'a_revoir' }),
    })

    const resultat = await annoterRegle(
      28,
      { reviewStatus: 'a_revoir', reviewNote: 'une note' },
      'ma-cle'
    )

    expect(fetch).toHaveBeenCalledWith(`${BASE_URL}/regles/28`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
        Authorization: 'Bearer ma-cle',
      },
      body: JSON.stringify({ review_status: 'a_revoir', review_note: 'une note' }),
    })
    expect(resultat).toEqual({ numero: 28, review_status: 'a_revoir' })
  })

  it('lève ErreurAuthentification sur 401', async () => {
    fetch.mockResolvedValue({ ok: false, status: 401, json: async () => ({}) })

    await expect(
      annoterRegle(28, { reviewStatus: 'a_revoir', reviewNote: 'x' }, 'mauvaise-cle')
    ).rejects.toBeInstanceOf(ErreurAuthentification)
  })

  it('lève une erreur classique avec le detail du corps sur 422', async () => {
    fetch.mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ detail: 'review_note est obligatoire' }),
    })

    await expect(
      annoterRegle(28, { reviewStatus: 'a_revoir', reviewNote: '' }, 'ma-cle')
    ).rejects.toThrow('review_note est obligatoire')
  })
})
