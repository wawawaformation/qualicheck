import { describe, it, expect, beforeEach, vi } from 'vitest'

// vi.resetModules() + import dynamique : useCleApi garde son état au niveau
// du module, donc chaque test a besoin d'une instance fraîche du module pour
// ne pas hériter de l'état laissé par le test précédent.
describe('useCleApi', () => {
  beforeEach(() => {
    localStorage.clear()
    vi.resetModules()
  })

  it('hasKey est faux sans clé enregistrée', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey } = useCleApi()
    expect(hasKey.value).toBe(false)
  })

  it('setKey enregistre la clé en localStorage et met hasKey à jour', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, cle, setKey } = useCleApi()

    setKey('ma-cle-secrete')

    expect(hasKey.value).toBe(true)
    expect(cle.value).toBe('ma-cle-secrete')
    expect(localStorage.getItem('qualicheck_regles_api_key')).toBe('ma-cle-secrete')
  })

  it('clearKey supprime la clé', async () => {
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, setKey, clearKey } = useCleApi()

    setKey('ma-cle-secrete')
    clearKey()

    expect(hasKey.value).toBe(false)
    expect(localStorage.getItem('qualicheck_regles_api_key')).toBeNull()
  })

  it('une clé déjà en localStorage au chargement du module est reprise', async () => {
    localStorage.setItem('qualicheck_regles_api_key', 'cle-existante')
    const { useCleApi } = await import('../../src/composables/useCleApi.js')
    const { hasKey, cle } = useCleApi()

    expect(hasKey.value).toBe(true)
    expect(cle.value).toBe('cle-existante')
  })
})
