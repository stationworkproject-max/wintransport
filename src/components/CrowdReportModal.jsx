import React, { useState, useMemo, useEffect } from 'react';
import { 
  AlertTriangle, 
  X, 
  CheckCircle, 
  Clock, 
  Users, 
  Wrench, 
  ShieldAlert, 
  Eye, 
  Search, 
  MapPin, 
  Navigation 
} from 'lucide-react';
import { STATIC_LINES as DEFAULT_STATIC_LINES } from '../data/staticTransit';
import { useTransitData } from '../context/TransitDataContext';
import { submitCrowdReport } from '../supabase';
import { getLineName, getLineShortName, getStationName } from '../utils/i18n';

function getDistanceMeters(lat1, lon1, lat2, lon2) {
  if (!lat1 || !lon1 || !lat2 || !lon2) return 999999;
  const R = 6371e3;
  const dLat = (lat2 - lat1) * Math.PI / 180;
  const dLon = (lon2 - lon1) * Math.PI / 180;
  const a =
    Math.sin(dLat / 2) * Math.sin(dLat / 2) +
    Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) *
    Math.sin(dLon / 2) * Math.sin(dLon / 2);
  const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  return Math.round(R * c);
}

export default function CrowdReportModal({ 
  isOpen, 
  onClose, 
  onReportSuccess, 
  userLocation = null,
  preselectedLine = null,
  language = 'fr' 
}) {
  const { lines: dynamicLines } = useTransitData();
  const STATIC_LINES = dynamicLines || DEFAULT_STATIC_LINES;

  const [lineId, setLineId] = useState('');
  const [reportType, setReportType] = useState('broken');
  const [severity, setSeverity] = useState('medium');
  const [stopName, setStopName] = useState('');
  const [message, setMessage] = useState('');
  const [direction, setDirection] = useState('');
  const [elapsedMinutes, setElapsedMinutes] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [showAllLines, setShowAllLines] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');

  // Calculate distance to all lines based on closest stop
  const linesWithDistance = useMemo(() => {
    return STATIC_LINES.map(line => {
      let minD = Infinity;
      let nearestStop = null;
      const allStops = [
        ...(line.stops || []),
        ...(line.stops_aller || []),
        ...(line.stops_retour || [])
      ];

      if (userLocation?.lat && userLocation?.lon) {
        for (const st of allStops) {
          if (st && st.lat && st.lon) {
            const d = getDistanceMeters(userLocation.lat, userLocation.lon, st.lat, st.lon);
            if (d < minD) {
              minD = d;
              nearestStop = st;
            }
          }
        }
      }

      return {
        ...line,
        distanceMeters: minD === Infinity ? 999999 : minD,
        nearestStop
      };
    }).sort((a, b) => a.distanceMeters - b.distanceMeters);
  }, [STATIC_LINES, userLocation]);

  // Nearest lines (within 3 km or top 8 closest)
  const nearbyLines = useMemo(() => {
    if (!userLocation?.lat || !userLocation?.lon) {
      return linesWithDistance.slice(0, 15);
    }
    const filtered = linesWithDistance.filter(l => l.distanceMeters <= 3000);
    return filtered.length >= 4 ? filtered : linesWithDistance.slice(0, 8);
  }, [linesWithDistance, userLocation]);

  // Effective lines displayed
  const displayedLines = useMemo(() => {
    let baseList = showAllLines ? linesWithDistance : nearbyLines;
    if (searchFilter.trim()) {
      const q = searchFilter.toLowerCase().trim();
      baseList = linesWithDistance.filter(l => 
        l.short_name.toLowerCase().includes(q) || 
        l.long_name.toLowerCase().includes(q)
      );
    }
    return baseList;
  }, [showAllLines, nearbyLines, linesWithDistance, searchFilter]);

  // Selected line object
  const currentSelectedLine = useMemo(() => {
    return STATIC_LINES.find(l => l.id === lineId) || displayedLines[0] || STATIC_LINES[0];
  }, [STATIC_LINES, lineId, displayedLines]);

  // Initialize selected line and stop
  useEffect(() => {
    if (preselectedLine?.id) {
      setLineId(preselectedLine.id);
      if (preselectedLine.directions && preselectedLine.directions[0]) {
        setDirection(preselectedLine.directions[0]);
      }
    } else if (nearbyLines.length > 0 && !lineId) {
      setLineId(nearbyLines[0].id);
      if (nearbyLines[0].nearestStop?.name) {
        setStopName(nearbyLines[0].nearestStop.name);
      }
      if (nearbyLines[0].directions && nearbyLines[0].directions[0]) {
        setDirection(nearbyLines[0].directions[0]);
      }
    }
  }, [preselectedLine?.id, nearbyLines]);

  // Update stops list when lineId changes
  useEffect(() => {
    if (currentSelectedLine) {
      const matchInDistance = linesWithDistance.find(l => l.id === currentSelectedLine.id);
      if (matchInDistance?.nearestStop?.name && !stopName) {
        setStopName(matchInDistance.nearestStop.name);
      }
      if (currentSelectedLine.directions && currentSelectedLine.directions[0] && !direction) {
        setDirection(currentSelectedLine.directions[0]);
      }
    }
  }, [currentSelectedLine?.id]);

  if (!isOpen) return null;

  const REPORT_TYPES = [
    { 
      id: 'broken', 
      label: language === 'ar' ? 'عطب أو مشكل فني' : 'Panne ou problème technique', 
      icon: Wrench, 
      color: 'text-red-400' 
    },
    { 
      id: 'delay', 
      label: language === 'ar' ? 'تأخير كبير' : 'Retard important', 
      icon: Clock, 
      color: 'text-orange-400' 
    },
    { 
      id: 'sighting', 
      label: language === 'ar' ? 'مرور مركبة (رأيتها بهذه المحطة)' : 'Vu à cette station (passage observé)', 
      icon: Eye, 
      color: 'text-cyan-400' 
    },
    { 
      id: 'crowded', 
      label: language === 'ar' ? 'ازدحام شديد / ممتلئ' : 'Forte affluence / Bondé', 
      icon: Users, 
      color: 'text-amber-400' 
    },
    { 
      id: 'accident', 
      label: language === 'ar' ? 'حادث أو تنبيه أمني' : 'Incident / Sécurité', 
      icon: ShieldAlert, 
      color: 'text-rose-400' 
    },
    { 
      id: 'normal', 
      label: language === 'ar' ? 'حركة عادية / سلسة' : 'Trafic normal / Fluide', 
      icon: CheckCircle, 
      color: 'text-emerald-400' 
    },
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      let finalMessage = message ? message.trim() : '';
      if (reportType === 'sighting') {
        const timeNote = elapsedMinutes === 0 
          ? (language === 'ar' ? 'الآن' : "à l'instant")
          : (language === 'ar' ? `منذ ${elapsedMinutes} د` : `il y a ${elapsedMinutes} min`);
        const dirNote = direction ? ` vers ${direction}` : '';
        const sightingPrefix = `[Passage observé ${timeNote}${dirNote}]`;
        finalMessage = finalMessage ? `${sightingPrefix} ${finalMessage}` : sightingPrefix;
      }

      await submitCrowdReport({
        line_id: lineId || currentSelectedLine?.id,
        stop_name: stopName || null,
        report_type: reportType,
        severity: (reportType === 'broken' || reportType === 'accident') ? 'high' : (reportType === 'delay' ? 'medium' : 'low'),
        message: finalMessage || null,
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
      alert(language === 'ar' ? 'خطأ أثناء إرسال البلاغ.' : "Erreur lors de l'envoi du signalement.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div 
      className="fixed inset-0 z-[1070] flex items-center justify-center p-3 sm:p-4 bg-slate-950/75 backdrop-blur-sm animate-fade-in pointer-events-auto"
      onClick={onClose}
    >
      <div 
        className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl sm:rounded-3xl shadow-2xl overflow-hidden text-slate-100 max-h-[92vh] flex flex-col"
        onClick={(e) => e.stopPropagation()}
      >
        
        {/* Header */}
        <div className="flex items-center justify-between p-4 sm:p-5 border-b border-slate-800 bg-slate-800/40">
          <div className="flex items-center gap-2.5">
            <div className="p-2.5 rounded-2xl bg-amber-500/20 text-amber-400">
              <AlertTriangle className="w-5 h-5" />
            </div>
            <div>
              <h2 className="font-bold text-base text-white">
                {language === 'ar' ? 'إبلاغ أو إشارة مرور' : 'Signaler un état de trafic'}
              </h2>
              <p className="text-xs text-slate-400">
                {language === 'ar' ? 'شارك المعلومة في الوقت الفعلي مع بقية المسافرين' : "Partagez l'info en temps réel avec la communauté"}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-200 hover:bg-slate-800"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {success ? (
          <div className="p-8 text-center space-y-3">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <CheckCircle className="w-6 h-6" />
            </div>
            <h3 className="font-bold text-lg text-white">
              {language === 'ar' ? 'تم إرسال الإشعار بنجاح !' : 'Signalement envoyé !'}
            </h3>
            <p className="text-xs text-slate-400">
              {language === 'ar' ? 'شكراً لمساهمتك في مساعدة المسافرين على هذا الخط.' : "Merci, vous venez d'aider les autres voyageurs sur la ligne."}
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1">
            
            {/* Proximity Lines Selector */}
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                  {language === 'ar' ? 'الخط المعني (الأقرب لموقعك)' : 'Lignes à proximité (les plus proches)'}
                </label>
                <button
                  type="button"
                  onClick={() => setShowAllLines(!showAllLines)}
                  className="text-[11px] text-blue-400 hover:text-blue-300 font-semibold"
                >
                  {showAllLines 
                    ? (language === 'ar' ? 'إظهار الأقرب فقط' : 'Afficher seulement les proches') 
                    : (language === 'ar' ? 'كافة الخطوط' : 'Toutes les lignes')}
                </button>
              </div>

              {/* Quick Search Bar */}
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none" />
                <input
                  type="text"
                  value={searchFilter}
                  onChange={(e) => setSearchFilter(e.target.value)}
                  placeholder={language === 'ar' ? 'ابحث عن خط أو حافلة...' : 'Rechercher une ligne (ex: Train, 1, 28, TGM)...'}
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl pl-8 pr-3 py-1.5 text-xs text-white placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
              </div>

              <select
                value={lineId || currentSelectedLine?.id}
                onChange={(e) => setLineId(e.target.value)}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {displayedLines.map((l) => (
                  <option key={l.id} value={l.id}>
                    {getLineShortName(l, language)} - {getLineName(l, language)} {l.distanceMeters < 50000 ? `(~${l.distanceMeters > 1000 ? (l.distanceMeters / 1000).toFixed(1) + 'km' : l.distanceMeters + 'm'})` : ''}
                  </option>
                ))}
              </select>
            </div>

            {/* Report Type Grid */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                {language === 'ar' ? 'نوع البلاغ' : 'Type de signalement'}
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {REPORT_TYPES.map((t) => {
                  const Icon = t.icon;
                  const isSelected = reportType === t.id;
                  return (
                    <button
                      key={t.id}
                      type="button"
                      onClick={() => setReportType(t.id)}
                      className={`p-2.5 rounded-xl border flex items-center gap-2.5 text-left transition-all ${
                        isSelected
                          ? 'bg-blue-600/25 border-blue-500 text-white ring-1 ring-blue-500'
                          : 'bg-slate-800/40 border-slate-700/60 text-slate-300 hover:bg-slate-800'
                      }`}
                    >
                      <Icon className={`w-4 h-4 flex-shrink-0 ${t.color}`} />
                      <span className="text-xs font-semibold leading-tight">{t.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Sighting Specific Controls: "Vu à cette station" */}
            {reportType === 'sighting' && (
              <div className="p-3.5 bg-cyan-950/30 border border-cyan-500/30 rounded-2xl space-y-3 animate-fade-in">
                <div className="flex items-center gap-2 text-cyan-300 text-xs font-bold">
                  <Eye className="w-4 h-4 text-cyan-400" />
                  <span>{language === 'ar' ? 'تفاصيل المرور المرصود بالعين' : 'Véhicule aperçu en station'}</span>
                </div>

                {/* Station Selection */}
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                    {language === 'ar' ? 'في أي محطة رأيت المركبة ؟' : 'À quelle station ?'}
                  </label>
                  <select
                    value={stopName}
                    onChange={(e) => setStopName(e.target.value)}
                    className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:ring-1 focus:ring-cyan-500"
                  >
                    <option value="">{language === 'ar' ? '-- اختر المحطة --' : '-- Choisir la station --'}</option>
                    {(currentSelectedLine?.stops || []).map((st) => (
                      <option key={st.id || st.name} value={st.name}>
                        {getStationName(st, language)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Direction */}
                {currentSelectedLine?.directions && currentSelectedLine.directions.length > 0 && (
                  <div>
                    <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                      {language === 'ar' ? 'في أي اتجاه ؟' : 'Direction observée'}
                    </label>
                    <div className="grid grid-cols-2 gap-1.5">
                      {currentSelectedLine.directions.map(dir => (
                        <button
                          key={dir}
                          type="button"
                          onClick={() => setDirection(dir)}
                          className={`p-2 rounded-lg text-xs font-semibold border transition ${
                            direction === dir
                              ? 'bg-cyan-600/30 border-cyan-400 text-cyan-100'
                              : 'bg-slate-800/60 border-slate-700 text-slate-400 hover:text-slate-200'
                          }`}
                        >
                          Vers {dir}
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {/* Elapsed Time Pills */}
                <div>
                  <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                    {language === 'ar' ? 'متى رأيتها ؟' : 'Vu il y a combien de temps ?'}
                  </label>
                  <div className="flex gap-1.5 flex-wrap">
                    {[
                      { mins: 0, label: language === 'ar' ? 'الآن' : "À l'instant" },
                      { mins: 2, label: language === 'ar' ? 'منذ 2 د' : 'Il y a 2 min' },
                      { mins: 5, label: language === 'ar' ? 'منذ 5 د' : 'Il y a 5 min' },
                      { mins: 10, label: language === 'ar' ? 'منذ 10 د' : 'Il y a 10 min' },
                      { mins: 15, label: language === 'ar' ? 'منذ 15 د' : 'Il y a 15 min' },
                    ].map(item => (
                      <button
                        key={item.mins}
                        type="button"
                        onClick={() => setElapsedMinutes(item.mins)}
                        className={`px-2.5 py-1 rounded-lg text-xs font-semibold border transition ${
                          elapsedMinutes === item.mins
                            ? 'bg-cyan-500 text-slate-950 border-cyan-400 font-bold'
                            : 'bg-slate-800/80 border-slate-700/80 text-slate-300 hover:text-white'
                        }`}
                      >
                        {item.label}
                      </button>
                    ))}
                  </div>
                </div>

              </div>
            )}

            {/* General Stop Name Input (if not sighting) */}
            {reportType !== 'sighting' && (
              <div>
                <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                  {language === 'ar' ? 'المحطة أو الموقع (اختياري)' : 'Station la plus proche (optionnel)'}
                </label>
                <input
                  type="text"
                  value={stopName}
                  onChange={(e) => setStopName(e.target.value)}
                  placeholder={language === 'ar' ? 'مثال: محطة برشلونة، حلق الوادي، رادس...' : 'Ex : Place Barcelone, La Goulette, Radès...'}
                  className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            )}

            {/* Message Details */}
            <div>
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider mb-1.5">
                {language === 'ar' ? 'تفاصيل إضافية (اختياري)' : 'Précision supplémentaire (optionnel)'}
              </label>
              <textarea
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder={language === 'ar' ? 'مثال: العربة الأخيرة أقل ازدحاماً، متوقف بسبب عطب...' : 'Ex : Prochaine rame dans 5 min, wagon de queue moins bondé...'}
                rows={2}
                className="w-full bg-slate-800/80 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className={`w-full py-3 px-4 font-bold text-sm rounded-xl shadow-lg flex items-center justify-center gap-2 transition-all disabled:opacity-50 ${
                reportType === 'sighting'
                  ? 'bg-cyan-500 hover:bg-cyan-400 text-slate-950 shadow-cyan-500/20'
                  : 'bg-amber-500 hover:bg-amber-400 text-slate-950 shadow-amber-500/20'
              }`}
            >
              {reportType === 'sighting' ? <Eye className="w-4 h-4" /> : <AlertTriangle className="w-4 h-4" />}
              <span>{loading ? (language === 'ar' ? 'جارٍ الإرسال...' : 'Publication...') : (language === 'ar' ? 'نشر البلاغ' : 'Publier le signalement')}</span>
            </button>

          </form>
        )}

      </div>
    </div>
  );
}
