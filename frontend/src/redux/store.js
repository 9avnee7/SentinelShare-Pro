// src/redux/store.js
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


const persistConfig = {
  key: 'root',
  storage,
  whitelist: ['user'],
  transforms: [
    encryptTransform({
      secretKey:import.meta.env.VITE_REDUX_SECRET_KEY, 
      onError: function (error) {
        console.error('Encryption error:', error)
      }
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
