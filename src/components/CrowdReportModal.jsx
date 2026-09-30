import React, { useState } from 'react';
import { AlertTriangle, X, CheckCircle, Clock, Users, Wrench, ShieldAlert } from 'lucide-react';
import { STATIC_LINES } from '../data/staticTransit';
import { submitCrowdReport } from '../supabase';
import { getLineName, getLineShortName } from '../utils/i18n';

export default function CrowdReportModal({ isOpen, onClose, onReportSuccess, language = 'fr' }) {
  const [lineId, setLineId] = useState('m1');
  const [reportType, setReportType] = useState('crowded');
  const [severity, setSeverity] = useState('medium');
  const [stopName, setStopName] = useState('');
  const [message, setMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isOpen) return null;

  const REPORT_TYPES = [
    { id: 'crowded', label: 'Forte affluence / Bondé', icon: Users, color: 'text-amber-400' },
    { id: 'delay', label: 'Retard important', icon: Clock, color: 'text-orange-400' },
    { id: 'broken', label: 'Panne ou problème technique', icon: Wrench, color: 'text-red-400' },
    { id: 'normal', label: 'Trafic normal / Fluide', icon: CheckCircle, color: 'text-emerald-400' },
    { id: 'accident', label: 'Incident / Sécurité', icon: ShieldAlert, color: 'text-rose-400' },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await submitCrowdReport({
        line_id: lineId,
        stop_name: stopName || null,
        report_type: reportType,
        severity: severity,
        message: message || null,
        upvotes: 1
      });

      setSuccess(true);
      setTimeout(() => {
        setSuccess(false);
        onClose();
        if (onReportSuccess) onReportSuccess();
      }, 1500);
    } catch (err) {
      console.error(err);
      alert("Erreur lors de l'envoi du signalement.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-[1070] flex items-center justify-center p-4 bg-slate-950/75 backdrop-blur-sm animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl overflow-hidden text-slate-100"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-800/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-amber-500/20 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-base text-white">Signaler un état de trafic</h2>
              <p className="text-xs text-slate-400">Partagez l'info en temps réel avec la communauté</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-white">Signalement envoyé !</h3>
            <p className="text-xs text-slate-400">Merci, vous venez d'aider les autres voyageurs sur la ligne.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-5 space-y-4">
            
            {/* Line Selection */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Ligne concernée
              </label>
              <select
                value={lineId}
                onChange={(e) => setLineId(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {STATIC_LINES.map((l) => (
                  <option key={l.id} value={l.id}>
                    {getLineShortName(l, language)} : {getLineName(l, language)}
                  </option>
                ))}
              </select>
            </div>

            {/* Report Type Grid */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Type de signalement
              </label>
              <div className="grid grid-cols-1 gap-2">
                {REPORT_TYPES.map((t) => {
                  const Icon = t.icon;
                  const isSelected = reportType === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setReportType(t.id)}
                      className={`p-2.5 rounded-xl border flex items-center gap-3 text-left transition-all ${
                        isSelected
                          ? 'bg-blue-600/20 border-blue-500 text-white ring-1 ring-blue-500'
                          : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <Icon className={`w-4 h-4 ${t.color}`} />
                      <span className="text-xs font-semibold">{t.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Optional Stop Name */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Station la plus proche (optionnel)
              </label>
              <input
                type="text"
                value={stopName}
                onChange={(e) => setStopName(e.target.value)}
                placeholder="Ex : Place Barcelone, La Goulette, Radès..."
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Message Details */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                Précision supplémentaire (optionnel)
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Ex : Prochaine rame dans 5 min, wagon de queue moins bondé..."
                rows={2}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-sm rounded-xl shadow-lg shadow-amber-500/20 flex items-center justify-center gap-2 transition-all disabled:opacity-50"
            >
              <AlertTriangle className="w-4 h-4" />
              <span>{loading ? 'Publication...' : 'Publier le signalement'}</span>
            </button>

          </form>
        )}

      </div>
    </div>
  );
}
