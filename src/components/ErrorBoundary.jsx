import React from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

export default class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null, errorInfo: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("Crash intercepté par ErrorBoundary:", error, errorInfo);
    this.setState({ errorInfo });
  }

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    localStorage.clear();
    sessionStorage.clear();
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-slate-900 text-white flex flex-col items-center justify-center p-6 text-center">
          <div className="w-16 h-16 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center mb-4">
            <AlertTriangle className="w-8 h-8" />
          </div>
          <h1 className="text-xl font-bold mb-2">Une erreur inattendue est survenue</h1>
          <p className="text-sm text-slate-400 max-w-sm mb-4">
            L'application a rencontré un problème d'affichage. Vous pouvez recharger la page ou réinitialiser les données locales.
          </p>
          <div className="bg-slate-800 p-3 rounded-lg text-left text-xs font-mono text-red-300 max-w-md w-full overflow-auto max-h-36 mb-6 border border-slate-700">
            {this.state.error?.toString() || 'Erreur inconnue'}
          </div>
          <div className="flex gap-3">
            <button
              onClick={this.handleReload}
              className="px-4 py-2 bg-red-600 hover:bg-red-500 text-white rounded-lg font-medium text-sm flex items-center gap-2 transition"
            >
              <RefreshCw className="w-4 h-4" />
              Recharger
            </button>
            <button
              onClick={this.handleReset}
              className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg font-medium text-sm transition"
            >
              Vider le cache
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}
