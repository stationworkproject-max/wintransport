// src/utils/i18n.js

export const TRANSLATIONS = {
  fr: {
    app_title: 'WinTransport TN',
    app_subtitle: 'Transports Publics Tunis',
    vehicles_live: 'véhicules en direct',
    by_community: 'par la communauté',
    i_am_onboard: 'Je suis à bord',
    onboard_active: 'À bord (GPS Actif)',
    report_problem: 'Signaler',
    trip_planner: 'Guide Trajet',
    enable_gps: 'Activer mon GPS',
    precise_gps: 'GPS Précis',
    my_location: 'Ma position GPS',
    gps_searching: 'Recherche des satellites GPS en cours...',
    all_networks: 'Tous les réseaux',
    all: 'Tous',
    buses: 'Bus',
    metros: 'Métros',
    trains: 'Trains & RFR',
    tab_map: 'Carte',
    tab_lines: 'Lignes',
    search_line_or_station: 'Rechercher une ligne ou station...',
    search_lines: 'Rechercher une ligne...',
    no_results: 'Aucun résultat trouvé',
    direction_aller: 'Sens Aller',
    direction_retour: 'Sens Retour',
    direction_label: 'Direction du trajet',
    stop_num: 'Arrêt',
    start: 'Départ',
    terminus: 'Terminus',
    stops_count: 'arrêts',
    click_to_isolate: 'Cliquez pour isoler la ligne',
    realtime_direct: 'véhicule(s) en direct',
    no_realtime: 'Aucun signal direct',
    switch_language: 'عربي',
    lang_code: 'fr',
    clear: 'Effacer',
  },
  ar: {
    app_title: 'WinTransport TN',
    app_subtitle: 'النقل العمومي بتونس الكبرى',
    vehicles_live: 'مركبة مباشرة',
    by_community: 'من المجتمع',
    i_am_onboard: 'أنا على متن الحافلة',
    onboard_active: 'على المتن (GPS نشط)',
    report_problem: 'إبلاغ عن عطب',
    trip_planner: 'تخطيط المسار',
    enable_gps: 'تفعيل الـ GPS',
    precise_gps: 'GPS دقيق',
    my_location: 'موقعي الحالي',
    gps_searching: 'جاري البحث عن إشارة GPS...',
    all_networks: 'كل الشبكات',
    all: 'الكل',
    buses: 'حافلات',
    metros: 'المترو',
    trains: 'قطارات و RFR',
    tab_map: 'الخريطة',
    tab_lines: 'الخطوط',
    search_line_or_station: 'بحث عن خط أو محطة...',
    search_lines: 'بحث عن خط...',
    no_results: 'لم يتم العثور على نتائج',
    direction_aller: 'اتجاه الذهاب',
    direction_retour: 'اتجاه الإياب',
    direction_label: 'اتجاه الخط',
    stop_num: 'المحطة',
    start: 'الانطلاق',
    terminus: 'نهاية الخط',
    stops_count: 'محطات',
    click_to_isolate: 'اضغط لعرض مسار الخط',
    realtime_direct: 'مركبة مباشرة الآن',
    no_realtime: 'لا توجد إشارة مباشرة',
    switch_language: 'FR',
    lang_code: 'ar',
    clear: 'إلغاء',
  }
};

export function getStationName(station, lang = 'fr') {
  if (!station) return '';
  if (lang === 'ar') {
    return station.name_ar || station.name || '';
  }
  return station.name_fr || station.name || '';
}

export function getLineName(line, lang = 'fr') {
  if (!line) return '';
  if (lang === 'ar') {
    return line.long_name_ar || line.long_name || '';
  }
  return line.long_name_fr || line.long_name || '';
}

export function getLineShortName(line, lang = 'fr') {
  if (!line) return '';
  if (lang === 'ar') {
    return line.short_name_ar || line.short_name || '';
  }
  return line.short_name || '';
}

export function getDirectionLabel(line, dirIdx = 0, lang = 'fr') {
  if (lang === 'ar') {
    if (line?.directions_ar && line.directions_ar[dirIdx]) {
      return line.directions_ar[dirIdx];
    }
    return dirIdx === 0 ? 'ذهاب' : 'إياب';
  }
  if (line?.directions_fr && line.directions_fr[dirIdx]) {
    return line.directions_fr[dirIdx];
  }
  if (line?.directions && line.directions[dirIdx]) {
    return line.directions[dirIdx];
  }
  return dirIdx === 0 ? 'Aller' : 'Retour';
}

export function t(key, lang = 'fr') {
  return TRANSLATIONS[lang]?.[key] || TRANSLATIONS['fr']?.[key] || key;
}
