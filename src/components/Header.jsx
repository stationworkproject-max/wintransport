import React from 'react';
import { 
  Radio, 
  MapPin, 
  AlertTriangle, 
  Train, 
  Bus, 
  Layers,
  Compass,
  Navigation,
  Sun,
  Moon
} from 'lucide-react';
export default function Header({
  activeNetwork,
  setActiveNetwork,
  liveCount,
  broadcastersCount = 0,
  passengersCount = 0,
  viewersCount = 1,
  onOpenBroadcast,
  isBroadcasting,
  onOpenReport,
  recentReportCount,
  userLocation,
  onRequestGps,
  gpsStatus,
  onOpenTripPlanner,
  language = 'fr',
  onToggleLanguage,
  theme = 'dark',
  onToggleTheme
}) {

  return (
    <header className="flex-shrink-0 sticky top-0 z-[1010] w-full glass-panel safe-top-padding px-3 sm:px-6 py-2 sm:py-2.5 pointer-events-auto transition-colors">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-2 sm:gap-3">
        
        {/* Brand & Live Counter */}
        <div className="flex items-center justify-between w-full md:w-auto gap-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 sm:w-10 sm:h-10 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-red-600 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white font-bold text-sm sm:text-base ring-1 ring-white/20 flex-shrink-0">
              TN
            </div>
            <div>
              <h1 className={`font-extrabold text-base sm:text-lg tracking-tight flex items-center gap-1.5 leading-none ${
                theme === 'light' ? 'text-slate-900' : 'text-white'
              }`}>
                WinTransport <span className="text-blue-500 font-black">TN</span>
              </h1>
              <div className={`text-[11px] flex items-center gap-2 mt-1 leading-none flex-wrap ${
                theme === 'light' ? 'text-slate-500' : 'text-slate-400'
              }`}>
                {/* Active Broadcasters */}
                <span className="flex items-center gap-1.5 text-emerald-500 font-semibold" title={language === 'ar' ? 'مركبات تبث GPS مباشرة' : 'Véhicules diffusant leur position GPS'}>
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span>{(broadcastersCount || liveCount || 0).toLocaleString()} {language === 'ar' ? 'مركبة' : 'véhicules'}</span>
                </span>

                <span className={theme === 'light' ? 'text-slate-300' : 'text-slate-700'}>•</span>

                {/* Hold users / passengers on board */}
                <span className={`flex items-center gap-1 font-semibold ${
                  theme === 'light' ? 'text-blue-600' : 'text-blue-400'
                }`} title={language === 'ar' ? 'ركاب متصلون على متن المركبات' : 'Voyageurs connectés à bord'}>
                  <span>👤 {(passengersCount || 0).toLocaleString()}</span>
                  <span className="text-[10px] font-normal opacity-90">{language === 'ar' ? 'على المتن' : 'à bord'}</span>
                </span>

                <span className={theme === 'light' ? 'text-slate-300' : 'text-slate-700'}>•</span>

                {/* Live Viewers */}
                <span className={`flex items-center gap-1 font-semibold ${
                  theme === 'light' ? 'text-indigo-600' : 'text-indigo-400'
                }`} title={language === 'ar' ? 'مستخدمون يتابعون الخريطة مباشرة' : 'Personnes connectées sur l\'application'}>
                  <span>👥 {(viewersCount || 1).toLocaleString()}</span>
                  <span className="text-[10px] font-normal opacity-90">{language === 'ar' ? 'متصل' : 'en ligne'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Mobile Action Buttons */}
          <div className="flex items-center gap-1.5 md:hidden">
            {/* Theme Switcher Mobile */}
            <button
              onClick={onToggleTheme}
              className={`p-2 rounded-xl border flex items-center justify-center transition-all ${
                theme === 'light'
                  ? 'bg-slate-100 border-slate-300 text-indigo-600 hover:bg-slate-200'
                  : 'bg-slate-800/90 border-slate-700 text-amber-400 hover:bg-slate-700'
              }`}
              title={theme === 'light' ? 'Mode sombre' : 'Mode clair'}
            >
              {theme === 'light' ? <Moon className="w-4 h-4" /> : <Sun className="w-4 h-4" />}
            </button>

            {/* Language Switcher Mobile */}
            <button
              onClick={onToggleLanguage}
              className={`px-2.5 py-1.5 rounded-xl border text-xs font-bold transition-all ${
                theme === 'light'
                  ? 'bg-blue-50 border-blue-200 text-blue-600 hover:bg-blue-100'
                  : 'bg-blue-600/20 border-blue-500/50 text-blue-300 hover:bg-blue-600/30'
              }`}
              title="Changer de langue / تغيير اللغة"
            >
              {language === 'ar' ? 'FR' : 'عربي'}
            </button>

            {/* Broadcast GPS Button */}
            <button
              onClick={onOpenBroadcast}
              className={`p-2 rounded-xl border flex items-center justify-center transition-all ${
                isBroadcasting
                  ? 'bg-emerald-500/20 border-emerald-500/50 text-emerald-400 animate-pulse'
                  : 'bg-blue-600 border-blue-500 text-white shadow-md shadow-blue-600/30'
              }`}
              title={language === 'ar' ? 'أنا على متن الحافلة' : 'Je suis à bord'}
            >
              <Radio className="w-4 h-4" />
            </button>
          </div>
        </div>



        {/* Desktop Action Buttons */}
        <div className="hidden md:flex items-center gap-2.5">
          {/* Theme Switcher Desktop */}
          <button
            onClick={onToggleTheme}
            className={`p-2 rounded-xl border flex items-center gap-1.5 transition-all text-xs font-semibold ${
              theme === 'light'
                ? 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-slate-700'
                : 'bg-slate-800/90 hover:bg-slate-700/90 border-slate-700 text-slate-300'
            }`}
            title={theme === 'light' ? 'Mode sombre' : 'Mode clair'}
          >
            {theme === 'light' ? (
              <>
                <Moon className="w-3.5 h-3.5 text-indigo-600" />
                <span className="hidden lg:inline">{language === 'ar' ? 'ليلي' : 'Sombre'}</span>
              </>
            ) : (
              <>
                <Sun className="w-3.5 h-3.5 text-amber-400" />
                <span className="hidden lg:inline">{language === 'ar' ? 'نهاري' : 'Clair'}</span>
              </>
            )}
          </button>

          {/* Language Switcher Desktop */}
          <button
            onClick={onToggleLanguage}
            className={`px-3 py-1.5 rounded-xl border text-xs font-bold flex items-center gap-1.5 transition-all shadow-sm ${
              theme === 'light'
                ? 'bg-slate-100 hover:bg-slate-200 border-slate-300 text-blue-600'
                : 'bg-slate-800/90 hover:bg-slate-700/90 border-slate-700 text-blue-400'
            }`}
            title="Changer de langue / تغيير اللغة"
          >
            <span className={`text-[10px] ${theme === 'light' ? 'text-slate-500' : 'text-slate-400'}`}>
              {language === 'ar' ? 'اللغة:' : 'Lang:'}
            </span>
            <span className="font-extrabold">{language === 'ar' ? 'العربية (FR)' : 'FR (عربي)'}</span>
          </button>

          {/* Real Live Community Tracking Status / GPS Indicator */}
          {userLocation ? (
            <div className={`hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl border text-xs ${
              theme === 'light'
                ? 'bg-emerald-50 border-emerald-300 text-slate-700'
                : 'bg-slate-800/60 border-emerald-500/40 text-slate-300'
            }`}>
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span className={`font-semibold ${theme === 'light' ? 'text-slate-900' : 'text-white'}`}>
                {language === 'ar' ? 'GPS دقيق' : 'GPS Précis'}
              </span>
              <span className={theme === 'light' ? 'text-slate-400' : 'text-slate-500'}>•</span>
              <span className="text-emerald-600 dark:text-emerald-400 font-medium">±{Math.round(userLocation.accuracy || 10)}m</span>
            </div>
          ) : (
            <button
              onClick={onRequestGps}
              className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-xl bg-blue-600/20 hover:bg-blue-600/30 border border-blue-500/50 text-xs text-blue-500 dark:text-blue-300 font-semibold transition-all"
              title="Activer la géolocalisation GPS"
            >
              <Navigation className="w-3.5 h-3.5 text-blue-500" />
              <span>{language === 'ar' ? 'تفعيل الـ GPS' : 'Activer mon GPS'}</span>
            </button>
          )}

          {/* Guide Trajet Button */}
          {onOpenTripPlanner && (
            <button
              onClick={onOpenTripPlanner}
              className={`px-3 py-1.5 rounded-xl border text-xs font-semibold flex items-center gap-1.5 transition-all ${
                theme === 'light'
                  ? 'bg-indigo-50 hover:bg-indigo-100 border-indigo-200 text-indigo-700'
                  : 'bg-indigo-600/20 hover:bg-indigo-600/30 border-indigo-500/40 text-indigo-300'
              }`}
            >
              <Compass className="w-3.5 h-3.5 text-indigo-500" />
              <span>{language === 'ar' ? 'دليل المسار' : 'Guide Trajet'}</span>
            </button>
          )}

          {/* Report Button */}
          <button
            onClick={onOpenReport}
            className={`px-3 py-1.5 rounded-xl border text-xs font-semibold text-amber-500 flex items-center gap-1.5 transition-all ${
              theme === 'light'
                ? 'bg-slate-100 hover:bg-slate-200 border-slate-300'
                : 'bg-slate-800/80 hover:bg-slate-700/80 border-slate-700'
            }`}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            <span>{language === 'ar' ? 'إبلاغ' : 'Signaler'}</span>
            {recentReportCount > 0 && (
              <span className="ml-0.5 bg-amber-500 text-slate-950 px-1.5 py-0.2 rounded-full text-[10px] font-bold">
                {recentReportCount}
              </span>
            )}
          </button>

          {/* Passenger On-Board Broadcast Button */}
          <button
            onClick={onOpenBroadcast}
            className={`px-3.5 py-2 rounded-xl text-xs font-bold flex items-center gap-2 transition-all shadow-md ${
              isBroadcasting
                ? 'bg-emerald-500 text-slate-950 shadow-emerald-500/30 animate-pulse'
                : 'bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white shadow-blue-500/25 ring-1 ring-white/10'
            }`}
          >
            <Radio className="w-3.5 h-3.5" />
            <span>{isBroadcasting ? (language === 'ar' ? 'على المتن (GPS نشط)' : 'À bord (GPS Actif)') : (language === 'ar' ? 'أنا على متن الحافلة' : 'Je suis à bord')}</span>
          </button>
        </div>

      </div>
    </header>
  );
}

