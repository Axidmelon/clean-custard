import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Link, useNavigate } from "react-router-dom";
import { BarChart3, Eye, EyeOff, Mail } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useAuth } from "@/contexts/auth-hooks";
import { getApiBaseUrl, APP_CONFIG } from "@/lib/constants";
import { logUserAction, logError } from "@/lib/logger";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showForgotPassword, setShowForgotPassword] = useState(false);
  const [forgotPasswordEmail, setForgotPasswordEmail] = useState("");
  const [isSendingReset, setIsSendingReset] = useState(false);
  const [loginFailed, setLoginFailed] = useState(false);
  const navigate = useNavigate();
  const { toast } = useToast();
  const { login } = useAuth();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setLoginFailed(false);

    try {
      // Call the backend login API
      const response = await fetch(`${getApiBaseUrl()}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const loginData = await response.json();
      logUserAction("Login successful", { email: loginData.email });
      
      // Use the auth context to store user data
      login(loginData.user, loginData.access_token);
      
      toast({
        title: "Login successful",
        description: "Welcome back to Custard Analytics!",
      });
      
      navigate("/");
    } catch (error) {
      logError("Login failed", error);
      const errorMessage = error instanceof Error ? error.message : "Invalid email or password. Please try again.";
      
      // Check if it's an authentication error to show forgot password option
      if (errorMessage.includes("Invalid email or password")) {
        setLoginFailed(true);
        setForgotPasswordEmail(email); // Pre-fill with the email they tried to login with
      }
      
      toast({
        title: "Login failed",
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    if (!forgotPasswordEmail.trim()) {
      toast({
        title: "Email required",
        description: "Please enter your email address.",
        variant: "destructive",
      });
      return;
    }

    setIsSendingReset(true);

    try {
      const response = await fetch(`${getApiBaseUrl()}/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: forgotPasswordEmail,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to send reset email');
      }

      toast({
        title: "Reset email sent",
        description: "If an account with that email exists, a password reset link has been sent.",
      });

      setShowForgotPassword(false);
      setForgotPasswordEmail("");
    } catch (error) {
      logError("Forgot password failed", error);
      toast({
        title: "Error",
        description: "Failed to send reset email. Please try again.",
        variant: "destructive",
      });
    } finally {
      setIsSendingReset(false);
    }
  };

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
          <p className="text-muted-foreground">Welcome back! Sign in to your account</p>
        </div>

        {/* Login Form */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your email and password to access your dashboard
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    if (loginFailed) setLoginFailed(false); // Reset login failed state when user types
                  }}
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => {
                      setPassword(e.target.value);
                      if (loginFailed) setLoginFailed(false); // Reset login failed state when user types
                    }}
                    required
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                  >
                    {showPassword ? (
                      <EyeOff className={APP_CONFIG.UI.ICON_SM} />
                    ) : (
                      <Eye className={APP_CONFIG.UI.ICON_SM} />
                    )}
                  </Button>
                </div>
              </div>

              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? "Signing In..." : "Sign In"}
              </Button>
            </form>

            {/* Show forgot password link when login fails */}
            {loginFailed && (
              <div className="mt-3 p-3 bg-muted/50 rounded-md border border-muted">
                <p className="text-sm text-muted-foreground mb-2">Having trouble signing in?</p>
                <Button
                  variant="link"
                  className="h-auto p-0 text-primary text-sm font-medium"
                  onClick={() => setShowForgotPassword(true)}
                >
                  Reset your password
                </Button>
              </div>
            )}

            <div className="mt-4 text-center text-sm">
              <span className="text-muted-foreground">Don't have an account? </span>
              <Link to="/signup" className="text-primary hover:underline font-medium">
                Sign up
              </Link>
            </div>
          </CardContent>
        </Card>

        <div className="text-center">
          <Link to="/" className="text-sm text-muted-foreground hover:underline">
            ← Back to home
          </Link>
        </div>
      </div>

      {/* Forgot Password Dialog */}
      <Dialog open={showForgotPassword} onOpenChange={setShowForgotPassword}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Mail className={APP_CONFIG.UI.ICON_MD} />
              Reset Password
            </DialogTitle>
            <DialogDescription>
              Enter your email address and we'll send you a link to reset your password.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="reset-email">Email</Label>
              <Input
                id="reset-email"
                type="email"
                placeholder="Enter your email"
                value={forgotPasswordEmail}
                onChange={(e) => setForgotPasswordEmail(e.target.value)}
                disabled={isSendingReset}
              />
            </div>
          </div>
          <DialogFooter className="flex-col sm:flex-row gap-2">
            <Button
              variant="outline"
              onClick={() => {
                setShowForgotPassword(false);
                setForgotPasswordEmail("");
              }}
              disabled={isSendingReset}
            >
              Cancel
            </Button>
            <Button onClick={handleForgotPassword} disabled={isSendingReset}>
              {isSendingReset ? "Sending..." : "Send Reset Link"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}