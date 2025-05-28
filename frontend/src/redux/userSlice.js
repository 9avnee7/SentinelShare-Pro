// src/redux/userSlice.js
import { createSlice } from '@reduxjs/toolkit'

const initialState = {
  userInfo: null,
  accessToken: null,
  isLoggedIn: false
}

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setAuthState: (state, action) => {
      state.userInfo = action.payload.userInfo
      state.accessToken = action.payload.accessToken
      state.isLoggedIn = true
    },
    clearAuthState: (state) => {
      state.userInfo = null
      state.accessToken = null
      state.isLoggedIn = false
    }
  }
})

export const { setAuthState, clearAuthState } = userSlice.actions
export default userSlice.reducer
