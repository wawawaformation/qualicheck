import { describe, it, expect, beforeEach, vi } from 'vitest'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const ICI = dirname(fileURLToPath(import.meta.url))
const CAS = readFileSync(join(ICI, 'regles_api_client_acceptance.jsonl'), 'utf-8')
  .trim()
  .split('\n')
  .map((ligne) => JSON.parse(ligne))

describe('acceptance — boucle de revue (regles_api_client_acceptance.jsonl)', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
    vi.unstubAllGlobals()
  })

  it.each(CAS)('$scenario', async (cas) => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { useRegles } = await import('../../src/composables/useRegles.js')

    if (cas.a_cle) {
      useCleApi().setKey('cle-de-test')
    }

    vi.stubGlobal(
      'fetch',
      vi.fn(async (_url, options) => {
        if (options?.method === 'PATCH') {
          return {
            ok: cas.reponse_patch_statut === 200,
            status: cas.reponse_patch_statut,
            json: async () => cas.reponse_patch_corps ?? { detail: 'Erreur serveur' },
          }
        }
        return { ok: true, status: 200, json: async () => [] }
      })
    )

    const { annoter, dernierResultat, redirectionCleApi } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'Note de test' })

    if (cas.resultat_attendu === 'redirection_cle_api') {
      expect(redirectionCleApi.value).toBe(true)
    } else {
      expect(dernierResultat.value).toBe(cas.resultat_attendu)
    }
  })
})
