import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotification } from '../hooks/useNotification';
import { apiService } from '../services/api';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/Card';
import { Sparkles, KeyRound, User } from 'lucide-react';

export const Login = () => {
  const { login } = useAuth();
  const { addToast } = useNotification();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const validate = () => {
    const newErrors = {};
    if (!username.trim()) newErrors.username = 'Username is required';
    if (!password) newErrors.password = 'Password is required';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    try {
      await apiService.login(username, password);
      login(username, password);
      addToast('Successfully connected to  backend!', 'success');
    } catch (err) {
      console.error(err);
      const msg = err.response?.data?.detail || 'Failed to authenticate. Please check your credentials.';
      addToast(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-tr from-background via-slate-900/10 to-indigo-950/10 px-4">
      {/* Dynamic Background Blur */}
      <div className="absolute top-1/4 left-1/4 h-72 w-72 rounded-full bg-primary/10 blur-3xl" />
      <div className="absolute bottom-1/4 right-1/4 h-72 w-72 rounded-full bg-indigo-500/10 blur-3xl" />

      <Card className="w-full max-w-md shadow-2xl relative z-10 border-border/80">
        <CardHeader className="text-center pt-8 pb-4">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20 mb-3 animate-bounce">
            <img src="public/logo.svg" className="h-6 w-6" />
          </div>
          <CardTitle className="text-2xl font-extrabold tracking-tight bg-gradient-to-r from-foreground to-foreground/80 bg-clip-text">
            Connexion
          </CardTitle>
          <CardDescription className="text-sm text-muted-foreground mt-1">
            Connectez-vous pour accéder au tableau de bord client
          </CardDescription>
        </CardHeader>
        <CardContent className="pb-8">
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="relative">
              <Input
                id="username"
                label="Identifiant"
                placeholder="Entrez votre username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                error={errors.username}
                className="pl-10"
              />
              <User className="absolute left-3 bottom-3.5 h-4.5 w-4.5 text-muted-foreground/60" />
            </div>

            <div className="relative">
              <Input
                id="password"
                type="password"
                label="Mot de passe"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                error={errors.password}
                className="pl-10"
              />
              <KeyRound className="absolute left-3 bottom-3.5 h-4.5 w-4.5 text-muted-foreground/60" />
            </div>

            <Button
              type="submit"
              loading={loading}
              className="w-full mt-2"
              size="lg"
            >
              Se connecter
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
