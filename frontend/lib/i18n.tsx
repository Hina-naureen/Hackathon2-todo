'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

export type Lang = 'en' | 'ur'

const translations = {
  en: {
    appName: 'Evolution of Todo',
    myTasks: 'My Tasks',
    addTask: '+ Add Task',
    noTasks: 'No tasks yet. Add your first task.',
    taskSingular: 'task',
    taskPlural: 'tasks',
    completed: 'Completed',
    pending: 'Pending',
    signOut: 'Sign out',
    titleLabel: 'Title',
    descriptionLabel: 'Description',
    cancel: 'Cancel',
    saveChanges: 'Save changes',
    addTaskBtn: 'Add Task',
    addTaskHeading: 'Add Task',
    editTaskHeading: 'Edit Task',
    deleteTask: 'Delete task',
    willBeRemoved: 'will be permanently removed.',
    cannotBeUndone: 'This cannot be undone.',
    delete: 'Delete',
    deleting: 'Deleting…',
    saving: 'Saving…',
    titleRequired: 'Title is required.',
    titleTooLong: 'Title must be 200 characters or fewer.',
    descTooLong: 'Description must be 500 characters or fewer.',
    taskPlaceholder: 'Task title',
    descPlaceholder: 'Optional description',
    chatAsk: 'Ask anything…',
    chatWaiting: 'Waiting for reply…',
    aiAssistant: 'AI Assistant',
    createTask: 'Create Task',
    adding: 'Adding…',
    voiceOn: 'TTS On',
    voiceOff: 'TTS Off',
    listening: 'Listening…',
    somethingWentWrong: 'Something went wrong.',
    failedToCreate: 'Failed to create task. Please try again.',
    taskAdded: 'added to your list!',
    language: 'اردو',
  },
  ur: {
    appName: 'ٹوڈو کا ارتقاء',
    myTasks: 'میرے کام',
    addTask: '+ کام شامل کریں',
    noTasks: 'ابھی کوئی کام نہیں۔ پہلا کام شامل کریں۔',
    taskSingular: 'کام',
    taskPlural: 'کام',
    completed: 'مکمل',
    pending: 'باقی',
    signOut: 'سائن آؤٹ',
    titleLabel: 'عنوان',
    descriptionLabel: 'تفصیل',
    cancel: 'منسوخ',
    saveChanges: 'تبدیلیاں محفوظ کریں',
    addTaskBtn: 'کام شامل کریں',
    addTaskHeading: 'کام شامل کریں',
    editTaskHeading: 'کام تبدیل کریں',
    deleteTask: 'کام حذف کریں',
    willBeRemoved: 'ہمیشہ کے لیے حذف ہو جائے گا۔',
    cannotBeUndone: 'یہ واپس نہیں ہو سکتا۔',
    delete: 'حذف کریں',
    deleting: 'حذف ہو رہا ہے…',
    saving: 'محفوظ ہو رہا ہے…',
    titleRequired: 'عنوان ضروری ہے۔',
    titleTooLong: 'عنوان 200 حروف سے کم ہونا چاہیے۔',
    descTooLong: 'تفصیل 500 حروف سے کم ہونی چاہیے۔',
    taskPlaceholder: 'کام کا عنوان',
    descPlaceholder: 'اختیاری تفصیل',
    chatAsk: 'کچھ بھی پوچھیں…',
    chatWaiting: 'جواب کا انتظار ہے…',
    aiAssistant: 'AI معاون',
    createTask: 'کام بنائیں',
    adding: 'شامل ہو رہا ہے…',
    voiceOn: 'آواز چالو',
    voiceOff: 'آواز بند',
    listening: 'سن رہا ہے…',
    somethingWentWrong: 'کچھ غلط ہوا۔',
    failedToCreate: 'کام بنانے میں ناکامی۔ دوبارہ کوشش کریں۔',
    taskAdded: 'آپ کی فہرست میں شامل ہو گیا!',
    language: 'EN',
  },
}

export type TranslationKey = keyof typeof translations.en

interface LanguageContextType {
  lang: Lang
  setLang: (lang: Lang) => void
  t: (key: TranslationKey) => string
  isRTL: boolean
}

const LanguageContext = createContext<LanguageContextType | null>(null)

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [lang, setLang] = useState<Lang>('en')
  const isRTL = lang === 'ur'

  function t(key: TranslationKey): string {
    return translations[lang][key] ?? translations.en[key]
  }

  return (
    <LanguageContext.Provider value={{ lang, setLang, t, isRTL }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useLanguage(): LanguageContextType {
  const ctx = useContext(LanguageContext)
  if (!ctx) throw new Error('useLanguage must be used within LanguageProvider')
  return ctx
}
