import { describe, it, expect, vi, beforeEach } from 'vitest'
import { useRegles } from '../../src/composables/useRegles.js'
import { ErreurAuthentification } from '../../src/services/reglesApiService.js'

vi.mock('../../src/services/reglesApiService.js', async () => {
  const actual = await vi.importActual('../../src/services/reglesApiService.js')
  return {
    ...actual,
    listerRegles: vi.fn(),
    annoterRegle: vi.fn(),
  }
})
vi.mock('../../src/composables/useCleApi.js', () => ({
  useCleApi: vi.fn(),
}))

import { listerRegles, annoterRegle } from '../../src/services/reglesApiService.js'
import { useCleApi } from '../../src/composables/useCleApi.js'

const REGLE_28 = {
  numero: 28,
  intitule: 'Le formulaire de contact confirme la bonne soumission des données',
  theme: 'Formulaires',
  outils: ['statique', 'playwright'],
  phases: ['Développement'],
  review_status: null,
  review_note: null,
}
const REGLE_65 = {
  numero: 65,
  intitule: 'Les liens ne sont pas soulignés en dehors du texte courant',
  theme: 'Liens',
  outils: ['vision'],
  phases: ['Conception'],
  review_status: 'valide',
  review_note: null,
}

describe('useRegles — chargement et filtrage', () => {
  beforeEach(() => {
    listerRegles.mockResolvedValue([REGLE_28, REGLE_65])
  })

  it('charger() remplit reglesBrutes', async () => {
    const { reglesBrutes, charger } = useRegles()
    await charger()
    expect(reglesBrutes.value).toEqual([REGLE_28, REGLE_65])
  })

  it('reglesFiltrees applique la recherche texte', async () => {
    const { reglesFiltrees, recherche, charger } = useRegles()
    await charger()
    recherche.value = 'formulaire'
    expect(reglesFiltrees.value).toEqual([REGLE_28])
  })

  it('reglesFiltrees applique le filtre outil en OU', async () => {
    const { reglesFiltrees, filtreOutil, charger } = useRegles()
    await charger()
    filtreOutil.value = ['vision']
    expect(reglesFiltrees.value).toEqual([REGLE_65])
  })

  it('reglesFiltrees applique le filtre revue, "aucun" = review_status null', async () => {
    const { reglesFiltrees, filtreReviewStatus, charger } = useRegles()
    await charger()
    filtreReviewStatus.value = ['aucun']
    expect(reglesFiltrees.value).toEqual([REGLE_28])
  })

  it('themesDisponibles liste les thèmes uniques triés', async () => {
    const { themesDisponibles, charger } = useRegles()
    await charger()
    expect(themesDisponibles.value).toEqual(['Formulaires', 'Liens'])
  })
})

describe('useRegles — annotation', () => {
  it('sans clé API, redirige sans appeler le service', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: false }, cle: { value: null }, clearKey: vi.fn() })
    const { annoter, redirectionCleApi } = useRegles()

    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(annoterRegle).not.toHaveBeenCalled()
    expect(redirectionCleApi.value).toBe(true)
  })

  it('avec une clé valide, met à jour reglesBrutes et dernierResultat', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'ma-cle' }, clearKey: vi.fn() })
    listerRegles.mockResolvedValue([REGLE_28])
    annoterRegle.mockResolvedValue({ ...REGLE_28, review_status: 'a_revoir', review_note: 'x' })

    const { charger, reglesBrutes, dernierResultat, annoter } = useRegles()
    await charger()
    const resultat = await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(resultat).toBe('succes')
    expect(dernierResultat.value).toBe('succes')
    expect(reglesBrutes.value[0].review_status).toBe('a_revoir')
  })

  it('annoter deux fois de suite la même règle renvoie "succes" les deux fois', async () => {
    // Régression : dernierResultat passe à 'succes' puis reste à 'succes' au
    // second appel (même valeur) — un watch(dernierResultat) ne détecterait
    // pas ce second succès. La valeur de retour, elle, est fiable à chaque appel.
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'ma-cle' }, clearKey: vi.fn() })
    annoterRegle.mockResolvedValue({ ...REGLE_28, review_status: 'a_revoir', review_note: 'x' })

    const { annoter } = useRegles()
    const premier = await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })
    const second = await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'y' })

    expect(premier).toBe('succes')
    expect(second).toBe('succes')
  })

  it('sur ErreurAuthentification, efface la clé et redirige', async () => {
    const clearKey = vi.fn()
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'cle-perimee' }, clearKey })
    annoterRegle.mockRejectedValue(new ErreurAuthentification('invalide'))

    const { annoter, redirectionCleApi } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(clearKey).toHaveBeenCalled()
    expect(redirectionCleApi.value).toBe(true)
  })

  it('sur erreur serveur, expose dernierResultat=erreur avec le message', async () => {
    useCleApi.mockReturnValue({ hasKey: { value: true }, cle: { value: 'ma-cle' }, clearKey: vi.fn() })
    annoterRegle.mockRejectedValue(new Error('Échec de l\'annotation (500)'))

    const { annoter, dernierResultat, erreurAnnotation } = useRegles()
    await annoter(28, { reviewStatus: 'a_revoir', reviewNote: 'x' })

    expect(dernierResultat.value).toBe('erreur')
    expect(erreurAnnotation.value).toBe('Échec de l\'annotation (500)')
  })
})
