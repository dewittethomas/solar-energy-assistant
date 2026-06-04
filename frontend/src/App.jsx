import { Suspense, lazy, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { api } from './api/client.js'
import { LoginFlow } from './components/auth/LoginFlow.jsx'
import { AppLayout } from './components/layout/AppLayout.jsx'
import { useProductionDataStatus } from './hooks/useProductionDataStatus.js'

const AssistantPage = lazy(() => import('./pages/AssistantPage.jsx').then((module) => ({ default: module.AssistantPage })))
const AnalysisPage = lazy(() => import('./pages/AnalysisPage.jsx').then((module) => ({ default: module.AnalysisPage })))
const ConfigurationPage = lazy(() => import('./pages/ConfigurationPage.jsx').then((module) => ({ default: module.ConfigurationPage })))
const DashboardPage = lazy(() => import('./pages/DashboardPage.jsx').then((module) => ({ default: module.DashboardPage })))
const DataManagementPage = lazy(() => import('./pages/DataManagementPage.jsx').then((module) => ({ default: module.DataManagementPage })))
const ForecastsPage = lazy(() => import('./pages/ForecastsPage.jsx').then((module) => ({ default: module.ForecastsPage })))
const ModelsPage = lazy(() => import('./pages/ModelsPage.jsx').then((module) => ({ default: module.ModelsPage })))
const TrainingProgressPage = lazy(() => import('./pages/TrainingProgressPage.jsx').then((module) => ({ default: module.TrainingProgressPage })))

const pages = {
  dashboard: DashboardPage,
  forecasts: ForecastsPage,
  models: ModelsPage,
  dataManagement: DataManagementPage,
  assistant: AssistantPage,
  analysis: AnalysisPage,
  configuration: ConfigurationPage,
  training: TrainingProgressPage,
}

const onboardingPages = {
  onboardingInstallation: 'installation',
  onboardingOwner: 'owner',
}

const defaultConsumingActivities = [
  { id: 'washing_machine', name: 'Wasmachine', consumption_kwh: 1.1, duration_minutes: 90, category: 'laundry', is_custom: false },
  { id: 'dishwasher', name: 'Vaatwasser', consumption_kwh: 1.2, duration_minutes: 90, category: 'kitchen', is_custom: false },
  { id: 'dryer', name: 'Droger', consumption_kwh: 2.5, duration_minutes: 120, category: 'laundry', is_custom: false },
  { id: 'boiler', name: 'Boiler', consumption_kwh: 3, duration_minutes: 180, category: 'heating', is_custom: false },
  { id: 'ev_charging', name: 'Elektrische wagen laden', consumption_kwh: 7, duration_minutes: 180, category: 'mobility', is_custom: false },
]

export default function App() {
  const { i18n } = useTranslation()
  const initialRoute = parseRoute()
  const [activePage, setActivePage] = useState(initialRoute.activePage)
  const [activeTrainingRunId, setActiveTrainingRunId] = useState(initialRoute.trainingRunId)
  const [modelState, setModelState] = useState(initialRoute.trainingRunId ? 'training' : 'no_data')
  const [preferences, setPreferences] = useState({ darkMode: false, developerMode: false, language: 'nl' })
  const [installation, setInstallation] = useState({
    capacityKwp: null,
    city: '',
    country: 'Belgium',
    id: null,
    installationKwp: null,
    name: '',
    panelCount: null,
  })
  const [consumingActivities, setConsumingActivities] = useState(defaultConsumingActivities)
  const [availableConsumingActivities, setAvailableConsumingActivities] = useState(defaultConsumingActivities)
  const [currentOwner, setCurrentOwner] = useState(null)
  const [bootError, setBootError] = useState('')
  const [isBooting, setIsBooting] = useState(true)
  const [isSubmittingOnboarding, setIsSubmittingOnboarding] = useState(false)
  const ActivePage = pages[activePage]
  const currentSessionUser = mapOwnerAndInstallationToSession(currentOwner, installation)
  const datasetState = useProductionDataStatus(currentSessionUser.installationId, modelState)

  useEffect(() => {
    function handlePopState() {
      const nextRoute = parseRoute()
      setActivePage(nextRoute.activePage)
      setActiveTrainingRunId(nextRoute.trainingRunId)

      if (nextRoute.trainingRunId) {
        setModelState('training')
      }
    }

    window.addEventListener('popstate', handlePopState)
    return () => window.removeEventListener('popstate', handlePopState)
  }, [])

  useEffect(() => {
    async function bootApp() {
      setIsBooting(true)
      setBootError('')

      try {
        const owner = await api.getOwner().catch((error) => {
          if (error.status === 404) {
            return null
          }

          throw error
        })

        if (!owner) {
          setCurrentOwner(null)
          navigate('onboardingOwner')
          return
        }

        setCurrentOwner(owner)
        const configuration = await api.getActiveInstallation().catch((error) => {
          if (error.status === 404) {
            return null
          }

          throw error
        })

        if (!configuration) {
          navigate('onboardingInstallation')
          return
        }

        applyConfiguration(configuration)
        navigate(initialRoute.activePage === 'training' ? 'training' : 'dashboard', {
          replace: true,
          trainingRunId: initialRoute.trainingRunId,
        })
      } catch (error) {
        setBootError(error.message)
        navigate('onboardingOwner')
      } finally {
        setIsBooting(false)
      }
    }

    bootApp()
  }, [])

  useEffect(() => {
    if (isBooting) {
      return
    }

    if (!currentOwner && activePage !== 'onboardingOwner') {
      navigate('onboardingOwner', { replace: true })
      return
    }

    if (currentOwner && !installation.id && activePage === 'onboardingOwner') {
      navigate('onboardingInstallation', { replace: true })
      return
    }

    if (currentOwner && installation.id && onboardingPages[activePage]) {
      navigate('dashboard', { replace: true })
    }
  }, [activePage, currentOwner, installation.id, isBooting])

  function updatePreferences(nextPreferences) {
    setPreferences((currentPreferences) => {
      const resolvedPreferences =
        typeof nextPreferences === 'function' ? nextPreferences(currentPreferences) : nextPreferences

      if (resolvedPreferences.language !== currentPreferences.language) {
        i18n.changeLanguage(resolvedPreferences.language)
      }

      return resolvedPreferences
    })
  }

  async function createOwner(ownerPayload) {
    setIsSubmittingOnboarding(true)

    try {
      const owner = await api.createOwner(ownerPayload)
      setCurrentOwner(owner)
      navigate('onboardingInstallation')
    } finally {
      setIsSubmittingOnboarding(false)
    }
  }

  async function createInstallation(installationPayload) {
    setIsSubmittingOnboarding(true)

    try {
      const createdInstallation = await api.createInstallation(installationPayload)
      applyConfiguration(createdInstallation)
      navigate('dashboard')
    } finally {
      setIsSubmittingOnboarding(false)
    }
  }

  async function resetLocalState() {
    await api.resetLocalState()
    setCurrentOwner(null)
    setModelState('no_data')
    setActiveTrainingRunId(null)
    setInstallation({
      capacityKwp: null,
      city: '',
      country: 'Belgium',
      id: null,
      installationKwp: null,
      name: '',
      panelCount: null,
    })
    setConsumingActivities(defaultConsumingActivities)
    setAvailableConsumingActivities(defaultConsumingActivities)
    navigate('onboardingOwner', { replace: true })
  }

  async function deleteOwner() {
    await api.deleteOwner()
    setCurrentOwner(null)
    setModelState('no_data')
    navigate('onboardingOwner', { replace: true })
  }

  function applyConfiguration(configuration) {
    setInstallation({
      capacityKwp: configuration.capacity_kwp ?? configuration.installation_kwp ?? null,
      city: normalizeLocation(configuration.city || ''),
      country: configuration.country || 'Belgium',
      id: configuration.installation_id || configuration.id || null,
      installationKwp: configuration.installation_kwp ?? configuration.capacity_kwp ?? null,
      name: configuration.name || 'Thuisinstallatie',
      panelCount: configuration.panel_count ?? null,
    })
    setAvailableConsumingActivities(
      configuration.available_consuming_activities?.length
        ? configuration.available_consuming_activities.map(normalizeActivityForState)
        : defaultConsumingActivities,
    )
    setConsumingActivities(
      configuration.consuming_activities?.length
        ? configuration.consuming_activities.map(normalizeActivityForState)
        : defaultConsumingActivities,
    )
  }

  function saveConfiguration(nextInstallation = installation, nextActivities = consumingActivities) {
    if (!installation.id) {
      return
    }

    api.saveConfiguration(installation.id, {
      capacity_kwp: nextInstallation.capacityKwp ?? nextInstallation.installationKwp ?? null,
      city: nextInstallation.city || null,
      consuming_activities: nextActivities.map(normalizeActivity),
      country: nextInstallation.country || null,
      installation_kwp: nextInstallation.installationKwp ?? nextInstallation.capacityKwp ?? null,
      name: nextInstallation.name || null,
      panel_count: nextInstallation.panelCount ?? null,
    }).catch(() => {})
  }

  function updateInstallation(nextInstallation) {
    setInstallation((currentInstallation) => {
      const resolvedInstallation =
        typeof nextInstallation === 'function' ? nextInstallation(currentInstallation) : nextInstallation

      saveConfiguration(resolvedInstallation, consumingActivities)
      return resolvedInstallation
    })
  }

  function updateConsumingActivities(nextActivities) {
    setConsumingActivities((currentActivities) => {
      const resolvedActivities = typeof nextActivities === 'function' ? nextActivities(currentActivities) : nextActivities

      saveConfiguration(installation, resolvedActivities)
      return resolvedActivities
    })
  }

  async function uploadDataset(payload) {
    return api.uploadDataset(payload)
  }

  async function startTrainingForDatasetUpload(uploadResult) {
    const trainingRun = await resolveTrainingRun(uploadResult)

    if (trainingRun?.training_run_id) {
      navigate('training', { trainingRunId: trainingRun.training_run_id })
    }
  }

  async function resolveTrainingRun(result) {
    if (result?.training_run_id) {
      return result
    }

    if (result?.parquet_path) {
      return api.trainModelFromParquet(result.parquet_path)
    }

    return null
  }

  function navigate(page, options = {}) {
    const trainingRunId = options.trainingRunId || (page === 'training' ? activeTrainingRunId : null)
    setActivePage(page)

    if (page === 'training') {
      setActiveTrainingRunId(trainingRunId)
      setModelState('training')
      updateHistory(trainingRunId ? `/training/${trainingRunId}` : '/training', options.replace)
      return
    }

    updateHistory(resolvePath(page), options.replace)
  }

  function handleTrainingStatusChange(trainingRun) {
    if (trainingRun?.training_run_id) {
      setActiveTrainingRunId(trainingRun.training_run_id)
    }

    if (trainingRun?.status === 'completed') {
      setModelState('ready')
      return
    }

    if (trainingRun?.status === 'failed') {
      setModelState('failed')
      return
    }

    setModelState('training')
  }

  if (isBooting) {
    return (
      <main className="login-page onboarding-page">
        <section className="login-panel onboarding-panel">
          <div className="login-header onboarding-header">
            <div>
              <p className="eyebrow">{bootError ? 'SolarWise' : 'SolarWise opstarten'}</p>
              <h1>SolarWise</h1>
              <p>{bootError || 'We laden je profiel en installatie.'}</p>
            </div>
          </div>
        </section>
      </main>
    )
  }

  if (!currentOwner || onboardingPages[activePage]) {
    return (
      <LoginFlow
        initialStep={onboardingPages[activePage] || (currentOwner ? 'installation' : 'owner')}
        isBusy={isSubmittingOnboarding}
        onCreateInstallation={createInstallation}
        onCreateOwner={createOwner}
      />
    )
  }

  return (
    <AppLayout
      activePage={activePage}
      darkMode={preferences.darkMode}
      onNavigate={navigate}
      user={currentSessionUser}
    >
      <Suspense fallback={<PageFallback />}>
        <ActivePage
          availableConsumingActivities={availableConsumingActivities}
          consumingActivities={consumingActivities}
          installation={installation}
          modelState={modelState}
          datasetState={datasetState}
          onConsumingActivitiesChange={updateConsumingActivities}
          onInspectDataset={api.inspectDataset}
          onInstallationChange={updateInstallation}
          onNavigate={navigate}
          onPreferencesChange={updatePreferences}
          onDeleteOwner={deleteOwner}
          onResetLocalState={resetLocalState}
          onTrainingStatusChange={handleTrainingStatusChange}
          onStartTraining={startTrainingForDatasetUpload}
          onUploadDataset={uploadDataset}
          preferences={preferences}
          trainingRunId={activeTrainingRunId}
          user={currentSessionUser}
        />
      </Suspense>
    </AppLayout>
  )
}

function PageFallback() {
  return <p className="muted-message">SolarWise laden...</p>
}

function normalizeActivity(activity) {
  return {
    id: activity.id || null,
    name: translateActivityName(activity),
    consumption_kwh: Number(activity.consumption_kwh) || 0,
    duration_minutes: Number(activity.duration_minutes) || null,
    category: activity.category || (activity.is_custom ? 'custom' : null),
    is_custom: Boolean(activity.is_custom),
  }
}

function normalizeActivityForState(activity) {
  const defaultActivity = defaultConsumingActivities.find(
    (candidate) => candidate.id === activity.id || candidate.name === translateActivityName(activity),
  )

  return {
    id: activity.id || defaultActivity?.id || null,
    name: translateActivityName(activity),
    consumption_kwh: Number(activity.consumption_kwh) || defaultActivity?.consumption_kwh || 0,
    duration_minutes: Number(activity.duration_minutes) || defaultActivity?.duration_minutes || 60,
    category: activity.category || defaultActivity?.category || (activity.is_custom ? 'custom' : null),
    is_custom: Boolean(activity.is_custom),
  }
}

function translateActivityName(activity) {
  const key = activity.id || activity.name
  const names = {
    boiler: 'Boiler',
    Dishwasher: 'Vaatwasser',
    dishwasher: 'Vaatwasser',
    Dryer: 'Droger',
    dryer: 'Droger',
    'EV charging': 'Elektrische wagen laden',
    ev_charging: 'Elektrische wagen laden',
    laptop_charging: 'Laptop opladen',
    oven: 'Oven',
    'Washing machine': 'Wasmachine',
    washing_machine: 'Wasmachine',
  }

  return names[key] || activity.name
}

function mapOwnerAndInstallationToSession(owner, installation) {
  return {
    id: owner?.id || null,
    installationId: installation.id,
    installationKwp: installation.installationKwp,
    location: installation.city || '',
    name: owner?.display_name || [owner?.first_name, owner?.last_name].filter(Boolean).join(' '),
    panelCount: installation.panelCount,
  }
}

function normalizeLocation(location) {
  return location === 'Brussels' ? 'Brussel' : location
}

function parseRoute() {
  const path = window.location.pathname
  const trainingMatch = path.match(/^\/training\/([^/]+)/)

  if (trainingMatch) {
    return { activePage: 'training', trainingRunId: decodeURIComponent(trainingMatch[1]) }
  }

  if (path === '/onboarding/owner') {
    return { activePage: 'onboardingOwner', trainingRunId: null }
  }

  if (path === '/onboarding/installation') {
    return { activePage: 'onboardingInstallation', trainingRunId: null }
  }

  const routeMap = {
    '/ai-model': 'models',
    '/dashboard': 'dashboard',
    '/data-uploads': 'dataManagement',
    '/instellingen': 'configuration',
    '/planner': 'assistant',
    '/productiehistoriek': 'analysis',
    '/voorspelling': 'forecasts',
  }

  return { activePage: routeMap[path] || 'dashboard', trainingRunId: null }
}

function resolvePath(page) {
  const pathMap = {
    analysis: '/productiehistoriek',
    assistant: '/planner',
    configuration: '/instellingen',
    dashboard: '/dashboard',
    dataManagement: '/data-uploads',
    forecasts: '/voorspelling',
    models: '/ai-model',
    onboardingInstallation: '/onboarding/installation',
    onboardingOwner: '/onboarding/owner',
  }

  return pathMap[page] || '/dashboard'
}

function updateHistory(path, replace = false) {
  if (replace) {
    window.history.replaceState({}, '', path)
    return
  }

  window.history.pushState({}, '', path)
}
