import { Toaster } from "@/components/ui/toaster";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "./contexts/AuthContext";
import { FileUploadProvider } from "./contexts/FileUploadContext";
import { AppLayout } from "./components/layout/AppLayout";
import ErrorBoundary from "./components/ErrorBoundaryWrapper";
import { globalErrorHandler } from "./lib/errorHandler";
import TalkData from "./pages/TalkData";
import Connections from "./pages/Connections";
import Uploads from "./pages/Uploads";
import Settings from "./pages/Settings";
import NotFound from "./pages/NotFound";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import EmailVerification from "./pages/EmailVerification";
import ResetPassword from "./pages/ResetPassword";
import { useEffect } from "react";
import { logDebug } from "./lib/logger";
import { statusManager } from "./hooks/useWebSocketStatus";

const queryClient = new QueryClient();

// Component to initialize status WebSocket connection
const StatusWebSocketInitializer = () => {
  useEffect(() => {
    // Initialize the status manager
    logDebug('Status WebSocket manager initialized');
  }, []);
  
  return null;
};

const App = () => {
  return (
    <ErrorBoundary 
      onError={(error, errorInfo) => {
        globalErrorHandler.reportError(error, { 
          componentStack: errorInfo.componentStack,
          errorBoundary: 'App'
        });
      }}
    >
      <QueryClientProvider client={queryClient}>
        <TooltipProvider>
          <AuthProvider>
            <FileUploadProvider>
              <StatusWebSocketInitializer />
              <Toaster />
              <BrowserRouter>
              <Routes>
                {/* Public Routes */}
                <Route path="/landing" element={<Landing />} />
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />
                <Route path="/verify-email" element={<EmailVerification />} />
                <Route path="/auth/reset-password" element={<ResetPassword />} />
                
                {/* Protected Routes */}
                <Route path="/" element={<AppLayout />}>
                  <Route index element={<TalkData />} />
                  <Route path="talk-data" element={<TalkData />} />
                  <Route path="uploads" element={<Uploads />} />
                  <Route path="connections" element={<Connections />} />
                  <Route path="settings" element={<Settings />} />
                </Route>
                
                {/* ADD ALL CUSTOM ROUTES ABOVE THE CATCH-ALL "*" ROUTE */}
                <Route path="*" element={<NotFound />} />
              </Routes>
              </BrowserRouter>
            </FileUploadProvider>
          </AuthProvider>
        </TooltipProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  );
};

export default App;
