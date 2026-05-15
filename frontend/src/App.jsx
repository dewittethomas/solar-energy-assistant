import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { AppLayout } from './components/layout/AppLayout.jsx'
import { AssistantPage } from './pages/AssistantPage.jsx'
import { DashboardPage } from './pages/DashboardPage.jsx'
import { DataManagementPage } from './pages/DataManagementPage.jsx'
import { ModelsPage } from './pages/ModelsPage.jsx'
import { ConfigurationPage } from './pages/ConfigurationPage.jsx'

const pages = {
  dashboard: DashboardPage,
  models: ModelsPage,
  dataManagement: DataManagementPage,
  assistant: AssistantPage,
  configuration: ConfigurationPage,
}

export default function App() {
  const { i18n } = useTranslation()
  const [activePage, setActivePage] = useState('dashboard')
  const [preferences, setPreferences] = useState({
    darkMode: false,
    language: 'nl',
  })
  const [installation, setInstallation] = useState({
    panelCount: 12,
    installationKwp: 5.4,
  })
  const [assistantConsumption, setAssistantConsumption] = useState({
    car: 11,
    washingMachine: 1.2,
    dishwasher: 1.4,
    dryer: 2.4,
    boiler: 3,
  })
  const ActivePage = pages[activePage]

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

  return (
    <AppLayout activePage={activePage} darkMode={preferences.darkMode} onNavigate={setActivePage}>
      <ActivePage
        assistantConsumption={assistantConsumption}
        installation={installation}
        onAssistantConsumptionChange={setAssistantConsumption}
        onInstallationChange={setInstallation}
        preferences={preferences}
        onPreferencesChange={updatePreferences}
      />
    </AppLayout>
  )
}
