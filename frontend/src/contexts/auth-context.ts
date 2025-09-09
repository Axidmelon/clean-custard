import { createContext } from 'react';
import { AuthContextType } from './auth-constants';

export const AuthContext = createContext<AuthContextType | undefined>(undefined);
