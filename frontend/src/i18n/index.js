import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import en from './locales/en.json'
import fr from './locales/fr.json'
import nl from './locales/nl.json'

i18n.use(initReactI18next).init({
  resources: {
    nl: { translation: nl },
    fr: { translation: fr },
    en: { translation: en },
  },
  lng: 'nl',
  fallbackLng: 'nl',
  interpolation: {
    escapeValue: false,
  },
})

export default i18n
