import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

import enCommon from './locales/en/common.json';
import enAuth from './locales/en/auth.json';
import mrCommon from './locales/mr/common.json';
import mrAuth from './locales/mr/auth.json';

const resources = {
  en: {
    common: enCommon,
    auth: enAuth,
  },
  mr: {
    common: mrCommon,
    auth: mrAuth,
  },
};

i18n.use(initReactI18next).init({
  resources,
  lng: 'en',
  fallbackLng: 'en',
  ns: ['common', 'auth'],
  defaultNS: 'common',
  interpolation: {
    escapeValue: false, // React already escapes by default
  },
});

export default i18n;
