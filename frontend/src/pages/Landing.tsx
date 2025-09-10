import { Button } from "@/components/ui/button";
import { Card, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Link } from "react-router-dom";
import { BarChart3, Database, Shield, MessageSquare, CheckCircle, ArrowRight } from "lucide-react";

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900 text-white">
      {/* Header */}
      <header className="border-b border-gray-700/40 bg-gray-900/80 backdrop-blur-sm">
        <div className="container mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className="w-8 h-8 bg-primary rounded-lg flex items-center justify-center">
              <BarChart3 className="w-5 h-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold text-white">Custard Analytics</span>
          </div>
          <div className="flex items-center space-x-3">
            <Button variant="outline" asChild className="text-gray-900 bg-white border-gray-300 hover:bg-gray-100 hover:text-gray-900">
              <Link to="/login">Login</Link>
            </Button>
            <Button asChild>
              <Link to="/signup">Sign Up</Link>
            </Button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-16">
        <div className="text-center space-y-8 max-w-4xl mx-auto">
          <div className="space-y-6">
            <h1 className="text-5xl font-bold text-white leading-tight">
              Ask Questions About Your Data
              <span className="text-blue-400 block">In Plain English</span>
            </h1>
            <p className="text-xl text-gray-300 max-w-2xl mx-auto">
              Get instant, accurate answers from your database using natural language. 
              No SQL knowledge required. Keep your data completely secure.
            </p>
            
            {/* Example */}
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-6 max-w-2xl mx-auto">
              <div className="text-left space-y-6">
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-base font-medium">You</span>
                  </div>
                  <p className="text-gray-200 italic text-lg leading-relaxed">"Show me our top 10 customers by revenue this month"</p>
                </div>
                <div className="flex items-start space-x-4">
                  <div className="w-10 h-10 bg-green-600 rounded-full flex items-center justify-center flex-shrink-0 mt-1">
                    <span className="text-white text-base font-medium">AI</span>
                  </div>
                  <p className="text-gray-200 text-lg leading-relaxed">Instantly generates and runs the SQL query, returning formatted results</p>
                </div>
              </div>
            </div>
          </div>

          <div className="flex items-center justify-center space-x-4">
            <Button size="lg" asChild>
              <Link to="/signup">Get Started Free</Link>
            </Button>
            <Button variant="outline" size="lg" asChild className="text-gray-900 bg-white border-gray-300 hover:bg-gray-100 hover:text-gray-900">
              <Link to="/login">Sign In</Link>
            </Button>
          </div>
        </div>

        {/* How It Works Section */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">How It Works (The Secure Way)</h2>
          <div className="grid md:grid-cols-3 gap-8">
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="w-12 h-12 bg-blue-600/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Database className="w-6 h-6 text-blue-400" />
                </div>
                <CardTitle className="text-white">1. Connect Your Database</CardTitle>
                <CardDescription className="text-gray-300">
                  Choose your database type (PostgreSQL, MySQL, MongoDB, Snowflake). 
                  We generate a secure Docker command for you to run in your environment.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="w-12 h-12 bg-green-600/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Shield className="w-6 h-6 text-green-400" />
                </div>
                <CardTitle className="text-white">2. Your Data Stays Secure</CardTitle>
                <CardDescription className="text-gray-300">
                  Your database credentials never leave your network. Our agent runs inside 
                  your environment with read-only access and encrypted communication.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="w-12 h-12 bg-purple-600/20 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <MessageSquare className="w-6 h-6 text-purple-400" />
                </div>
                <CardTitle className="text-white">3. Ask Questions Naturally</CardTitle>
                <CardDescription className="text-gray-300">
                  Type questions in plain English. Get instant, formatted results. 
                  No SQL knowledge needed.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>

        {/* Why Choose Custard AI */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">Why Choose Custard AI?</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <CardTitle className="text-lg text-white">Zero-Trust Security</CardTitle>
                </div>
                <CardDescription className="text-gray-300">
                  Your database credentials never leave your control. The agent runs in your environment, not ours.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <CardTitle className="text-lg text-white">Read-Only Safety</CardTitle>
                </div>
                <CardDescription className="text-gray-300">
                  Agents can only execute SELECT queries. Your data is protected from accidental modification.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <CardTitle className="text-lg text-white">Natural Language</CardTitle>
                </div>
                <CardDescription className="text-gray-300">
                  Ask questions like "What's our monthly revenue trend?" instead of writing complex SQL.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <CardTitle className="text-lg text-white">Multi-Database Support</CardTitle>
                </div>
                <CardDescription className="text-gray-300">
                  Works with PostgreSQL, MySQL, MongoDB, and Snowflake.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="bg-gray-800 border-gray-700">
              <CardHeader>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <CardTitle className="text-lg text-white">Real-Time Results</CardTitle>
                </div>
                <CardDescription className="text-gray-300">
                  Get instant answers with live connection monitoring.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>

        {/* Perfect For Section */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">Perfect For</h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Business Analysts</CardTitle>
                <CardDescription className="text-gray-300">Who need quick data insights</CardDescription>
              </CardHeader>
            </Card>
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Product Managers</CardTitle>
                <CardDescription className="text-gray-300">Tracking key metrics</CardDescription>
              </CardHeader>
            </Card>
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Developers</CardTitle>
                <CardDescription className="text-gray-300">Who want to query data without SQL</CardDescription>
              </CardHeader>
            </Card>
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Teams</CardTitle>
                <CardDescription className="text-gray-300">That need self-service data access</CardDescription>
              </CardHeader>
            </Card>
            <Card className="text-center bg-gray-800 border-gray-700">
              <CardHeader>
                <CardTitle className="text-white">Anyone</CardTitle>
                <CardDescription className="text-gray-300">Who wants to understand their data better</CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>

        {/* Get Started Section */}
        <div className="mt-20 text-center">
          <h2 className="text-3xl font-bold mb-8 text-white">Get Started in 3 Steps</h2>
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="space-y-4">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                1
              </div>
              <h3 className="text-xl font-semibold text-white">Sign up</h3>
              <p className="text-gray-300">for a free account</p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                2
              </div>
              <h3 className="text-xl font-semibold text-white">Connect</h3>
              <p className="text-gray-300">your database using our secure agent</p>
            </div>
            <div className="space-y-4">
              <div className="w-12 h-12 bg-blue-600 text-white rounded-full flex items-center justify-center mx-auto text-xl font-bold">
                3
              </div>
              <h3 className="text-xl font-semibold text-white">Start asking</h3>
              <p className="text-gray-300">questions about your data</p>
            </div>
          </div>
        </div>

        {/* Security First Section */}
        <div className="mt-20">
          <h2 className="text-3xl font-bold text-center mb-12 text-white">Security First</h2>
          <div className="bg-gray-800 border border-gray-600 rounded-xl p-8 max-w-4xl mx-auto">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-gray-200">Your credentials never leave your network</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-gray-200">Read-only access only</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-gray-200">Encrypted communication</span>
                </div>
              </div>
              <div className="space-y-4">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-gray-200">Sandboxed execution</span>
                </div>
                <div className="flex items-center space-x-3">
                  <CheckCircle className="w-5 h-5 text-green-400" />
                  <span className="text-gray-200">No data storage on our servers</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Final CTA */}
        <div className="mt-20 text-center">
          <h2 className="text-3xl font-bold mb-6 text-white">Ready to make your data accessible?</h2>
          <Button size="lg" asChild className="text-lg px-8 py-6">
            <Link to="/signup">
              Get Started Free
              <ArrowRight className="w-5 h-5 ml-2" />
            </Link>
          </Button>
          <p className="text-gray-300 mt-6 text-sm">
            Custard: Making data accessible through natural language while keeping it completely secure.
          </p>
        </div>
      </main>
    </div>
  );
}