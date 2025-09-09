export interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  is_verified: boolean;
}

export interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
  updateUser: (userData: Partial<User>) => void;
  isAuthenticated: boolean;
  isLoading: boolean;
  refreshToken: () => Promise<boolean>;
}

export interface AuthProviderProps {
  children: React.ReactNode;
}
