import { configureStore } from '@reduxjs/toolkit'
import userReducer from './userSlice'
import {
  persistStore,
  persistReducer,
  FLUSH,
  REHYDRATE,
  PAUSE,
  PERSIST,
  PURGE,
  REGISTER
} from 'redux-persist'
import storage from 'redux-persist/lib/storage' 
import { encryptTransform } from 'redux-persist-transform-encrypt'

const secretKey = import.meta.env.VITE_REDUX_SECRET_KEY

function validateSecretKey(key) {
  if (typeof key !== 'string' || key.trim() === '') {
    throw new Error('Redux Persist encryption secretKey is missing or empty')
  }
  if (key.length < 16) {
    throw new Error('Redux Persist encryption secretKey is too short, must be at least 16 characters')
  }
  const validChars = /^[A-Za-z0-9+/=]+$/
  if (!validChars.test(key)) {
    throw new Error('Redux Persist encryption secretKey contains invalid characters')
  }
  try {
    atob(key)
  } catch {
    throw new Error('Redux Persist encryption secretKey is not valid base64')
  }
  return true
}


try {
  validateSecretKey(secretKey)
} catch (error) {
  console.error(error)
}

const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['user'],
  transforms: [
    encryptTransform({
      secretKey,
      onError: (err) => console.error('Encryption error:', err)
    })
  ]
}

const persistedReducer = persistReducer(persistConfig, userReducer)

export const store = configureStore({
  reducer: {
    user: persistedReducer
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: [FLUSH, REHYDRATE, PAUSE, PERSIST, PURGE, REGISTER]
      }
    })
})

export const persistor = persistStore(store)
