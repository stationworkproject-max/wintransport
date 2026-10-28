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
  Navigation,
  LocateFixed,
  ShieldCheck
} from 'lucide-react';
import { STATIC_LINES as DEFAULT_STATIC_LINES } from '../data/staticTransit';
import TRANSIT_SHAPES_DEFAULT from '../data/transitShapes.json';
import { useTransitData } from '../context/TransitDataContext';
import { submitCrowdReport } from '../supabase';
import { getLineName, getLineShortName, getStationName } from '../utils/i18n';

// Major Terminus Hubs (Place de Barcelone, Tunis Marine, etc.)
const MAJOR_TERMINUS_HUBS = [
  { id: 'barcelone', name: 'Gare de Tunis / Barcelone', lat: 36.7952, lon: 10.1805, radius: 130 },
  { id: 'tunis_marine', name: 'Tunis Marine', lat: 36.8010, lon: 10.1906, radius: 100 },
  { id: 'passage', name: 'Passage / République', lat: 36.8055, lon: 10.1815, radius: 95 },
  { id: 'bab_saadoun', name: 'Bab Saadoun', lat: 36.8085, lon: 10.1585, radius: 95 },
];

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

function getDistanceToSegment(pLat, pLon, aLat, aLon, bLat, bLon) {
  const cosLat = Math.cos((aLat * Math.PI) / 180);
  const mPerDegLat = 111132;
  const mPerDegLon = 111132 * cosLat;
  const dx = (bLon - aLon) * mPerDegLon;
  const dy = (bLat - aLat) * mPerDegLat;
  const lenSq = dx * dx + dy * dy;
  if (lenSq === 0) return getDistanceMeters(pLat, pLon, aLat, aLon);
  const px = (pLon - aLon) * mPerDegLon;
  const py = (pLat - aLat) * mPerDegLat;
  let t = (px * dx + py * dy) / lenSq;
  t = Math.max(0, Math.min(1, t));
  const distX = px - (t * dx);
  const distY = py - (t * dy);
  return Math.round(Math.sqrt(distX * distX + distY * distY));
}

export default function CrowdReportModal({ 
  isOpen, 
  onClose, 
  onReportSuccess, 
  userLocation = null,
  onRequestGps = null,
  preselectedLine = null,
  language = 'fr' 
}) {
  const { lines: dynamicLines, shapes: dynamicShapes } = useTransitData();
  const STATIC_LINES = dynamicLines || DEFAULT_STATIC_LINES;
  const TRANSIT_SHAPES = dynamicShapes || TRANSIT_SHAPES_DEFAULT;

  const [lineId, setLineId] = useState('');
  const [reportType, setReportType] = useState('broken');
  const [stopName, setStopName] = useState('');
  const [message, setMessage] = useState('');
  const [direction, setDirection] = useState('');
  const [elapsedMinutes, setElapsedMinutes] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // Strict proximity threshold: User must be physically near the line (max 200m - 250m)
  // You cannot see or know if a bus/train is broken down or late from 2.5 km away!
  const maxAllowedDistance = useMemo(() => {
    const acc = Math.round(userLocation?.accuracy || 15);
    // Base 200m, capped at 250m for slightly degraded GPS
    return Math.min(250, Math.max(180, acc * 4));
  }, [userLocation?.accuracy]);

  // Precise distance from user GPS to a transit line (checks hub, physical track shapes, and stops)
  const calculateDistanceToLine = (line) => {
    if (!line || !userLocation?.lat || !userLocation?.lon) {
      return { minD: 999999, closestStop: null };
    }
    const uLat = userLocation.lat;
    const uLon = userLocation.lon;
    let minD = Infinity;
    let closestStop = null;

    // 1. Hub check (Barcelone, Tunis Marine, etc.)
    for (const hub of MAJOR_TERMINUS_HUBS) {
      const dToHub = getDistanceMeters(uLat, uLon, hub.lat, hub.lon);
      if (dToHub <= hub.radius) {
        const allStops = [
          ...(line.stops || []),
          ...(line.stops_aller || []),
          ...(line.stops_retour || [])
        ];
        const hubStop = allStops.find(s => s && s.lat && s.lon && getDistanceMeters(hub.lat, hub.lon, s.lat, s.lon) <= (hub.radius + 70));
        if (hubStop) {
          return { minD: 0, closestStop: hubStop };
        }
      }
    }

    // 2. High-definition physical route polylines
    const shapesToCheck = [
      TRANSIT_SHAPES[line.id],
      TRANSIT_SHAPES[line.id + '_aller'],
      TRANSIT_SHAPES[line.id + '_retour'],
      TRANSIT_SHAPES[line.id + '_0'],
      TRANSIT_SHAPES[line.id + '_1']
    ].filter(s => Array.isArray(s) && s.length > 1);

    for (const shape of shapesToCheck) {
      for (let i = 0; i < shape.length - 1; i++) {
        const ptA = shape[i];
        const ptB = shape[i + 1];
        const dSeg = getDistanceToSegment(uLat, uLon, ptA[0], ptA[1], ptB[0], ptB[1]);
        if (dSeg < minD) {
          minD = dSeg;
        }
      }
    }

    // 3. Stops
    const allStops = [
      ...(line.stops || []),
      ...(line.stops_aller || []),
      ...(line.stops_retour || [])
    ];

    for (let i = 0; i < allStops.length; i++) {
      const s = allStops[i];
      if (s && s.lat && s.lon) {
        const d = getDistanceMeters(uLat, uLon, s.lat, s.lon);
        if (d < minD) {
          minD = d;
          closestStop = s;
        }
      }
    }

    return { minD: Math.round(minD), closestStop };
  };

  // Compute exact physical distance to all lines
  const allLinesWithDistance = useMemo(() => {
    if (!userLocation?.lat || !userLocation?.lon) return [];
    return STATIC_LINES.map(line => {
      const { minD, closestStop } = calculateDistanceToLine(line);
      return {
        ...line,
        distanceMeters: minD,
        closestStop
      };
    }).sort((a, b) => a.distanceMeters - b.distanceMeters);
  }, [STATIC_LINES, userLocation, TRANSIT_SHAPES]);

  const nearestLine = allLinesWithDistance[0] || null;

  // STRICT FILTER: ONLY lines where user is physically NEAR (<= maxAllowedDistance, 200m - 250m)
  const nearbyLines = useMemo(() => {
    return allLinesWithDistance.filter(line => line.distanceMeters <= maxAllowedDistance);
  }, [allLinesWithDistance, maxAllowedDistance]);

  const isUserNearAnyLine = nearbyLines.length > 0;

  // Currently selected line
  const selectedLine = useMemo(() => {
    return nearbyLines.find(l => l.id === lineId) || nearbyLines[0] || null;
  }, [nearbyLines, lineId]);

  // Pre-select nearest line and stop
  useEffect(() => {
    if (preselectedLine?.id && nearbyLines.some(l => l.id === preselectedLine.id)) {
      setLineId(preselectedLine.id);
      if (preselectedLine.directions && preselectedLine.directions[0]) {
        setDirection(preselectedLine.directions[0]);
      }
    } else if (nearbyLines.length > 0) {
      setLineId(nearbyLines[0].id);
      if (nearbyLines[0].closestStop?.name) {
        setStopName(nearbyLines[0].closestStop.name);
      }
      if (nearbyLines[0].directions && nearbyLines[0].directions[0]) {
        setDirection(nearbyLines[0].directions[0]);
      }
    }
  }, [nearbyLines, preselectedLine?.id]);

  // Update stop and direction when selected line changes
  useEffect(() => {
    if (selectedLine) {
      if (selectedLine.closestStop?.name && !stopName) {
        setStopName(selectedLine.closestStop.name);
      }
      if (selectedLine.directions && selectedLine.directions[0] && !direction) {
        setDirection(selectedLine.directions[0]);
      }
    }
  }, [selectedLine?.id]);

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
    if (!selectedLine) return;

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
        line_id: selectedLine.id,
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
                {language === 'ar' ? 'مخصص للمسافرين المتواجدين بالقرب من الخط' : "Signalement réservé aux voyageurs sur place"}
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
        ) : !userLocation ? (
          /* PROXIMITY GATEKEEPER 1: GPS Required */
          <div className="p-6 text-center space-y-4 my-auto">
            <div className="w-14 h-14 rounded-3xl bg-amber-500/20 text-amber-400 mx-auto flex items-center justify-center border border-amber-500/30">
              <LocateFixed className="w-7 h-7 animate-pulse" />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-white">
                {language === 'ar' ? 'التحقق من الموقع GPS مطلوب' : 'Position GPS requise'}
              </h3>
              <p className="text-xs text-slate-400 mt-1 max-w-sm mx-auto leading-relaxed">
                {language === 'ar' 
                  ? 'للإبلاغ عن عطب أو تأخير، يجب تفعيل الـ GPS للتأكد من تواجدك الفعلي بالقرب من الخط لمنع البلاغات الوهمية.'
                  : "Pour garantir des signalements authentiques (panne, retard, passage), vous devez autoriser votre GPS afin de certifier votre présence à proximité de la ligne."}
              </p>
            </div>
            {onRequestGps && (
              <button
                type="button"
                onClick={onRequestGps}
                className="py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-bold text-sm rounded-2xl shadow-xl shadow-blue-500/30 transition active:scale-95 flex items-center gap-2 mx-auto"
              >
                <Navigation className="w-4 h-4" />
                <span>{language === 'ar' ? 'تفعيل وتحديث الـ GPS' : 'Activer mon GPS'}</span>
              </button>
            )}
          </div>
        ) : !isUserNearAnyLine ? (
          /* PROXIMITY GATEKEEPER 2: User is too far from any line (> 200-250m) */
          <div className="p-6 text-center space-y-4 my-auto">
            <div className="w-14 h-14 rounded-3xl bg-rose-500/10 text-rose-400 mx-auto flex items-center justify-center border border-rose-500/30">
              <MapPin className="w-7 h-7 animate-bounce" />
            </div>
            <div>
              <h3 className="font-extrabold text-base text-white">
                {language === 'ar' ? 'أنت بعيد عن خطوط النقل' : 'Aucun transport à proximité immédiate'}
              </h3>
              <p className="text-xs text-slate-300 mt-1.5 max-w-sm mx-auto leading-relaxed">
                {language === 'ar' 
                  ? `أنت على بعد أكثر من ${maxAllowedDistance} متر عن أي خط نقل. لا يمكن معرفة حالة حركة النقل أو الأعطال عن بعد.`
                  : `Vous vous trouvez à plus de ${maxAllowedDistance} mètres de tout tracé ou arrêt de transport.`}
              </p>
            </div>

            {nearestLine && (
              <div className="p-3 bg-slate-800/80 rounded-2xl border border-slate-700 max-w-sm mx-auto text-left space-y-2">
                <div className="text-[11px] uppercase tracking-wider font-bold text-slate-400 flex items-center justify-between">
                  <span>{language === 'ar' ? 'أقرب خط إليك' : 'Ligne la plus proche'}</span>
                  <span className="text-amber-400 font-extrabold">
                    {nearestLine.distanceMeters >= 1000 
                      ? `${(nearestLine.distanceMeters / 1000).toFixed(1)} km` 
                      : `${nearestLine.distanceMeters} m`}
                  </span>
                </div>
                <div className="flex items-center gap-2.5">
                  <span
                    className="px-2.5 py-1 rounded-xl text-white font-extrabold text-xs shadow flex-shrink-0"
                    style={{ backgroundColor: nearestLine.color }}
                  >
                    {nearestLine.short_name}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-bold text-xs text-white truncate">{nearestLine.long_name}</div>
                    <div className="text-[10px] text-slate-400 truncate">
                      {nearestLine.closestStop ? `Arrêt : ${nearestLine.closestStop.name}` : ''}
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="p-3 bg-red-950/40 rounded-2xl border border-red-500/40 text-xs text-red-200 max-w-sm mx-auto text-left flex items-start gap-2.5">
              <ShieldCheck className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
              <p className="leading-relaxed">
                {language === 'ar'
                  ? `حماية ضد البلاغات الخاطئة : للإبلاغ عن عطب أو تأخير أو مرور، يجب أن تكون متواجداً في عين المكان على بعد أقل من ${maxAllowedDistance} متر.`
                  : `Fiabilité communautaire : Pour empêcher les faux signalements à distance, vous devez être physiquement à l'arrêt ou sur la voie (distance ≤ ${maxAllowedDistance}m).`}
              </p>
            </div>

            {onRequestGps && (
              <button
                type="button"
                onClick={onRequestGps}
                className="py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-bold rounded-xl border border-slate-700 transition flex items-center gap-2 mx-auto"
              >
                <Navigation className="w-3.5 h-3.5 text-blue-400" />
                <span>{language === 'ar' ? 'تحديث الموقع GPS' : 'Actualiser ma position GPS'}</span>
              </button>
            )}
          </div>
        ) : (
          /* User is physically NEAR the line (<= 200m - 250m) */
          <form onSubmit={handleSubmit} className="p-4 sm:p-5 space-y-4 overflow-y-auto flex-1">
            
            {/* Verified Proximity Badge */}
            <div className="p-3 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl flex items-center justify-between text-xs">
              <div className="flex items-center gap-2 text-emerald-300 font-bold">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-ping"></span>
                <span>
                  {language === 'ar' 
                    ? `موقع معتمد بالقرب من الخط (${selectedLine?.distanceMeters || 0}م)` 
                    : `Position vérifiée à proximité immédiate (${selectedLine?.distanceMeters || 0}m)`}
                </span>
              </div>
              <span className="text-[10px] bg-emerald-950/80 px-2 py-0.5 rounded-full text-emerald-300 border border-emerald-500/40 font-mono">
                GPS ±{Math.round(userLocation?.accuracy || 15)}m
              </span>
            </div>

            {/* Line Selection (strictly limited to lines within near proximity) */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-300 uppercase tracking-wider">
                {language === 'ar' ? 'الخط القريب منك' : 'Ligne à votre portée'}
              </label>

              {nearbyLines.length > 1 ? (
                <div className="space-y-1.5">
                  <select
                    value={selectedLine?.id}
                    onChange={(e) => setLineId(e.target.value)}
                    className="w-full bg-slate-800/90 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    {nearbyLines.map((l) => (
                      <option key={l.id} value={l.id}>
                        {getLineShortName(l, language)} - {getLineName(l, language)} ({l.distanceMeters === 0 ? (language === 'ar' ? 'في المحطة' : 'À quai') : `à ${l.distanceMeters}m`})
                      </option>
                    ))}
                  </select>
                </div>
              ) : (
                <div className="p-3 bg-slate-800/60 border border-slate-700/80 rounded-2xl flex items-center gap-3">
                  <span
                    className="px-3 py-1.5 rounded-xl font-extrabold text-sm text-white flex-shrink-0 shadow"
                    style={{ backgroundColor: selectedLine?.color }}
                  >
                    {getLineShortName(selectedLine, language)}
                  </span>
                  <div className="min-w-0 flex-1">
                    <div className="font-bold text-xs truncate text-white">{getLineName(selectedLine, language)}</div>
                    <div className="text-[10px] text-slate-400 mt-0.5">
                      {selectedLine?.closestStop ? `${language === 'ar' ? 'محطة : ' : 'Arrêt : '}${selectedLine.closestStop.name}` : ''}
                    </div>
                  </div>
                  <span className="text-[10px] bg-emerald-500/20 text-emerald-400 font-bold px-2.5 py-1 rounded-full border border-emerald-500/30 flex-shrink-0">
                    {selectedLine?.distanceMeters === 0 ? (language === 'ar' ? 'في المحطة' : 'À quai') : `à ${selectedLine?.distanceMeters}m`}
                  </span>
                </div>
              )}
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
                    {(selectedLine?.stops || []).map((st) => (
                      <option key={st.id || st.name} value={st.name}>
                        {getStationName(st, language)}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Direction */}
                {selectedLine?.directions && selectedLine.directions.length > 0 && (
                  <div>
                    <label className="block text-[11px] font-bold text-slate-300 uppercase tracking-wider mb-1">
                      {language === 'ar' ? 'في أي اتجاه ؟' : 'Direction observée'}
                    </label>
                    <div className="grid grid-cols-2 gap-1.5">
                      {selectedLine.directions.map(dir => (
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
                  {language === 'ar' ? 'المحطة أو الموقع القريب (اختياري)' : 'Station la plus proche (optionnel)'}
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
