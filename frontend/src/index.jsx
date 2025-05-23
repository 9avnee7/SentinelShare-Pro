import { createContext, use } from "react"
import { useState } from "react";

export const GlobalContext=createContext(null);

const GlobalState=({children})=>{

    const [loggedIn, setLoggedIn] = useState(false); 
    const [accessToken,setAccessToken]=useState(null);
    const [userInfo, setUserInfo] = useState(null)
    const [loading, setLoading] = useState(false)
    const [redirectionPath,setRedirectionPath]=useState('dashboard');
    return  <GlobalContext.Provider

        value={{loggedIn, setLoggedIn ,loading,setLoading,accessToken,setAccessToken,userInfo,setUserInfo,redirectionPath,setRedirectionPath}}
    >
        {children}
    </GlobalContext.Provider>
}


export default GlobalState;