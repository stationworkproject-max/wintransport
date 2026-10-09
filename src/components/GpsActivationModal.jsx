import React, { useState } from 'react';
import { LocateFixed, Settings, X, RefreshCw, AlertTriangle, ShieldCheck, MapPin } from 'lucide-react';
import { isNativeAndroid, openLocationSettings, openAppSettings } from '../native/backgroundBroadcast';

export default function GpsActivationModal({
  isOpen,
  onClose,
  onRetryGps,
  language = 'fr',
  theme = 'dark'
}) {
  const [openingSettings, setOpeningSettings] = useState(false);
  const isAr = language === 'ar';

  if (!isOpen) return null;

  const handleOpenSettings = async () => {
    setOpeningSettings(true);
    try {
      if (isNativeAndroid()) {
        await openLocationSettings();
      } else {
        // Fallback for web: prompt user
        alert(isAr 
          ? "يرجى تفعيل خدمة الموقع (GPS) من شريط الإشعارات العلوي لهاتفك أو إعدادات المتصفح."
          : "Veuillez activer le GPS depuis le volet des raccourcis de votre téléphone ou dans les paramètres du navigateur.");
      }
    } catch (e) {
      try {
        await openAppSettings();
      } catch (err) {}
    } finally {
      setTimeout(() => setOpeningSettings(false), 1500);
    }
  };

  const handleRetry = () => {
    if (onRetryGps) {
      onRetryGps(true);
    }
    onClose();
  };

  return (
    <div 
      className="fixed inset-0 z-[1080] flex items-center justify-center p-3 sm:p-4 bg-slate-950/80 backdrop-blur-md animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className={`w-full max-w-md rounded-3xl border shadow-2xl overflow-hidden p-5 sm:p-6 transition-all animate-scale-up ${
          theme === 'light'
            ? 'bg-white border-slate-200 text-slate-900 shadow-blue-500/10'
            : 'bg-slate-900 border-slate-800 text-white shadow-2xl'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header with Icon and Close Button */}
        <div className="flex items-start justify-between gap-3 mb-4">
          <div className="relative flex items-center justify-center">
            <div className="absolute w-12 h-12 rounded-2xl bg-blue-500/20 animate-ping"></div>
            <div className="relative w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/30">
              <LocateFixed className="w-6 h-6 animate-pulse" />
            </div>
          </div>
          <button
            onClick={onClose}
            className={`p-2 rounded-xl transition ${
              theme === 'light'
                ? 'hover:bg-slate-100 text-slate-400 hover:text-slate-700'
                : 'hover:bg-slate-800 text-slate-400 hover:text-white'
            }`}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Title & Message */}
        <div className="space-y-2 mb-6">
          <h3 className="text-lg sm:text-xl font-extrabold tracking-tight">
            {isAr ? 'تفعيل نظام تحديد الموقع (GPS)' : 'Activer la localisation GPS'}
          </h3>
          <p className={`text-xs sm:text-sm leading-relaxed ${theme === 'light' ? 'text-slate-600' : 'text-slate-300'}`}>
            {isAr
              ? 'خدمة تحديد الموقع معطلة على هاتفك. لتتبع الحافلات والقطارات في الوقت الحقيقي وعرض مسارك بدقة، يرجى تفعيل الـ GPS.'
              : 'La localisation de votre téléphone est désactivée. Pour afficher votre position en temps réel, suivre les véhicules et guider vos trajets, veuillez activer votre GPS.'}
          </p>
        </div>

        {/* Steps Card */}
        <div className={`rounded-2xl p-3.5 mb-6 border text-xs space-y-2.5 ${
          theme === 'light' ? 'bg-slate-50 border-slate-200' : 'bg-slate-800/60 border-slate-700/60'
        }`}>
          <div className="flex items-center gap-2.5 text-blue-500 font-semibold">
            <span className="w-5 h-5 rounded-full bg-blue-500/20 flex items-center justify-center text-[10px] font-bold">1</span>
            <span>{isAr ? 'تفعيل مفتاح "الموقع" في إعدادات الهاتف' : 'Activer l\'interrupteur "Position / GPS"'}</span>
          </div>
          <div className="flex items-center gap-2.5 text-emerald-500 font-semibold">
            <span className="w-5 h-5 rounded-full bg-emerald-500/20 flex items-center justify-center text-[10px] font-bold">2</span>
            <span>{isAr ? 'السماح للتطبيق بالوصول للموقع الدقيق' : 'Autoriser la précision de localisation'}</span>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="space-y-2.5">
          <button
            onClick={handleOpenSettings}
            disabled={openingSettings}
            className="w-full flex items-center justify-center gap-2 py-3.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 active:scale-[0.98] text-white font-bold text-sm rounded-2xl shadow-xl shadow-blue-500/25 transition disabled:opacity-50"
          >
            <Settings className={`w-4 h-4 ${openingSettings ? 'animate-spin' : ''}`} />
            <span>
              {isAr ? 'فتح إعدادات الـ GPS في الهاتف' : 'Ouvrir les Paramètres GPS ⚙️'}
            </span>
          </button>

          <button
            onClick={handleRetry}
            className={`w-full flex items-center justify-center gap-2 py-3 px-4 font-semibold text-xs rounded-2xl transition border ${
              theme === 'light'
                ? 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'
                : 'bg-slate-800 hover:bg-slate-700 border-slate-700 text-slate-200'
            }`}
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>{isAr ? 'تحقق مرة أخرى' : 'Vérifier à nouveau / Réessayer'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
