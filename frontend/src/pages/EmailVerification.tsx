import { useEffect, useState } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { BarChart3, CheckCircle, XCircle, Loader2 } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/auth-hooks";
import { getApiBaseUrl, APP_CONFIG } from "@/lib/constants";
import { logUserAction, logError } from "@/lib/logger";

export default function EmailVerification() {
  const [searchParams] = useSearchParams();
  const [verificationStatus, setVerificationStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const navigate = useNavigate();
  const { toast } = useToast();
  const { login } = useAuth();

  useEffect(() => {
    const verifyEmail = async () => {
      const token = searchParams.get('token');
      
      if (!token) {
        setVerificationStatus('error');
        return;
      }

      try {
        // Call the backend verification API
        const response = await fetch(`${getApiBaseUrl()}/auth/verify?token=${token}`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Verification failed');
        }

        const result = await response.json();
        logUserAction("Email verification successful", { token });
        
        // Automatically log in the user
        login(result.user, result.access_token);
        
        setVerificationStatus('success');
        toast({
          title: "Email verified successfully!",
          description: "You have been automatically logged in. Welcome to Custard Analytics!",
        });
        
        // Redirect to dashboard after 2 seconds
        setTimeout(() => {
          navigate("/");
        }, APP_CONFIG.TIMEOUTS.EMAIL_VERIFICATION);
        
      } catch (error) {
        logError("Email verification failed", error);
        setVerificationStatus('error');
        toast({
          title: "Verification failed",
          description: error instanceof Error ? error.message : "The verification link is invalid or has expired.",
          variant: "destructive",
        });
      }
    };

    verifyEmail();
  }, [searchParams, navigate, toast, login]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 flex items-center justify-center p-4">
      <div className="w-full max-w-md space-y-6">
        {/* Logo */}
        <div className="text-center space-y-2">
          <div className="flex items-center justify-center space-x-2">
            <div className={`${APP_CONFIG.UI.CONTAINER_SM} bg-primary rounded-lg flex items-center justify-center`}>
              <BarChart3 className={`${APP_CONFIG.UI.ICON_LG} text-primary-foreground`} />
            </div>
            <span className="text-2xl font-bold text-foreground">Custard Analytics</span>
          </div>
        </div>

        <Card>
          <CardHeader className="text-center">
            {verificationStatus === 'loading' && (
              <>
                <div className={`${APP_CONFIG.UI.CONTAINER_MD} bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <Loader2 className={`${APP_CONFIG.UI.ICON_XL} text-primary animate-spin`} />
                </div>
                <CardTitle>Verifying Your Email</CardTitle>
                <CardDescription>
                  Please wait while we verify your email address...
                </CardDescription>
              </>
            )}
            
            {verificationStatus === 'success' && (
              <>
                <div className={`${APP_CONFIG.UI.CONTAINER_MD} bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <CheckCircle className={`${APP_CONFIG.UI.ICON_XL} text-green-600`} />
                </div>
                <CardTitle className="text-green-600">Email Verified!</CardTitle>
                <CardDescription>
                  Your email has been successfully verified and you've been automatically logged in. You'll be redirected to your dashboard shortly.
                </CardDescription>
              </>
            )}
            
            {verificationStatus === 'error' && (
              <>
                <div className={`${APP_CONFIG.UI.CONTAINER_MD} bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                  <XCircle className={`${APP_CONFIG.UI.ICON_XL} text-red-600`} />
                </div>
                <CardTitle className="text-red-600">Verification Failed</CardTitle>
                <CardDescription>
                  The verification link is invalid or has expired. Please try signing up again.
                </CardDescription>
              </>
            )}
          </CardHeader>
          
          <CardContent className="text-center space-y-4">
            {verificationStatus === 'success' && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">
                  Redirecting to dashboard in 2 seconds...
                </p>
                <Button asChild>
                  <Link to="/">Go to Dashboard Now</Link>
                </Button>
              </div>
            )}
            
            {verificationStatus === 'error' && (
              <div className="space-y-2">
                <Button asChild>
                  <Link to="/signup">Sign Up Again</Link>
                </Button>
                <div className="text-sm">
                  <Link to="/login" className="text-muted-foreground hover:underline">
                    Already have an account? Sign in
                  </Link>
                </div>
              </div>
            )}
            
            {verificationStatus === 'loading' && (
              <p className="text-sm text-muted-foreground">
                This may take a few moments...
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}