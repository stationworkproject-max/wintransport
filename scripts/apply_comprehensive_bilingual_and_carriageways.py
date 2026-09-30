import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

# 1. Dictionary of all 204 untranslated stops -> (name_fr, name_ar)
TRANSLATIONS_204 = {
    "CELLULOSE (SILOS)": ("Usine de Cellulose (Silos)", "مصنع السيلولوز (صوامع)"),
    "ECOLE HAMMED": ("École Hammed", "مدرسة حامد"),
    "NOUVELLE HAMMED": ("Nouvelle Hammed", "حامد الجديدة"),
    "DHNIBA": ("Dhniba", "ذنيبة"),
    "PARC MAYANA": ("Parc Mayana", "حديقة ميانة"),
    "DEPOT TEBOURBA": ("Dépôt Tébourba", "مستودع طبربة"),
    "GARDE NATIONALE TEBOURBA": ("Garde Nationale Tébourba", "الحرس الوطني طبربة"),
    "STEG TEBOURBA": ("STEG Tébourba", "الشركة التونسية للكهرباء والغاز طبربة"),
    "TERMINUS TEBOURBA": ("Terminus Tébourba", "نهاية الخط طبربة"),
    "LYCÉE CHABBAOU": ("Lycée Chabbaou", "معهد شباو"),
    "TERMINUS SIDI OTHMAN": ("Terminus Sidi Othman", "نهاية الخط سيدي عثمان"),
    "CAPITAINERIE": ("Capitainerie", "قبطانية الميناء"),
    "TERMINUS CITÉ CHAKER": ("Terminus Cité Chaker", "نهاية الخط حي شاكر"),
    "CROISEMENT JEBEL RASSAS": ("Croisement Jebel Rassas", "مفترق جبل الرصاص"),
    "AVIATION CIVILE": ("Aviation Civile", "الطيران المدني"),
    "CAFÉ EL FERDAOUS": ("Café El Ferdaous", "مقهى الفردوس"),
    "RELAIS BORJ EL AMRI-ALLER": ("Relais Borj El Amri (Aller)", "استراحة برج العامري (ذهاب)"),
    "MOSQUÉE BORJ EL AMRI-ALLER": ("Mosquée Borj El Amri (Aller)", "جامع برج العامري (ذهاب)"),
    "CAFE MEDINA-ALLER": ("Café Medina (Aller)", "مقهى المدينة (ذهاب)"),
    "CITE EL INTILAKA ": ("Cité El Intilaka", "حي الانطلاقة"),
    "CITE EL INTILAKA": ("Cité El Intilaka", "حي الانطلاقة"),
    "CAFE MEDINA 23/": ("Café Medina", "مقهى المدينة"),
    "MOSQUÉE BORJ EL AMRI-RETOUR": ("Mosquée Borj El Amri (Retour)", "جامع برج العامري (إياب)"),
    "RELAIS BORJ EL AMRI-RETOUR": ("Relais Borj El Amri (Retour)", "استراحة برج العامري (إياب)"),
    "CITE 26/26": ("Cité 26-26", "حي 26-26"),
    "AALOUINE1": ("Aalouine 1", "العلوين 1"),
    "AALOUINE2": ("Aalouine 2", "العلوين 2"),
    "MENZEL HBIB 23D-23/": ("Menzel Hbib", "منزل حبيب"),
    "MENZEL HBIB-ALLER": ("Menzel Hbib (Aller)", "منزل حبيب (ذهاب)"),
    "CROISEMENT DRIJET-ALLER": ("Croisement Drijet (Aller)", "مفترق دريجة (ذهاب)"),
    "ROUTE DRIJET-ALLER": ("Route Drijet (Aller)", "طريق دريجة (ذهاب)"),
    "DRIJET": ("Drijet", "دريجة"),
    "ROUTE DRIJET 23D-23/": ("Route Drijet", "طريق دريجة"),
    "CROISEMENT DRIJET 23D-23/": ("Croisement Drijet", "مفترق دريجة"),
    "KIOSQUE AGIL-ALLER": ("Kiosque Agil (Aller)", "محطة عجيل (ذهاب)"),
    "KM30-ALLER": ("Km 30 (Aller)", "الكيلومتر 30 (ذهاب)"),
    "MESSAADINE-ALLER": ("Messaadine (Aller)", "المساعدين (ذهاب)"),
    "FURNA-ALLER": ("Furna (Aller)", "فورنة (ذهاب)"),
    "ENTREE BORJ ENNOUR-ALLER": ("Entrée Borj Ennour (Aller)", "مدخل برج النور (ذهاب)"),
    "EPICIER JILANI-ALLER": ("Épicier Jilani (Aller)", "بقالة الجيلاني (ذهاب)"),
    "ENTREE GRIAAT-ALLER": ("Entrée Griaat (Aller)", "مدخل القريعات (ذهاب)"),
    "GRIAAT": ("Griaat", "القريعات"),
    "ENTREE GRIAAT-RETOUR": ("Entrée Griaat (Retour)", "مدخل القريعات (إياب)"),
    "EPICIER JILANI-RETOUR": ("Épicier Jilani (Retour)", "بقالة الجيلاني (إياب)"),
    "ENTREE BORJ ENNOUR-RETOUR": ("Entrée Borj Ennour (Retour)", "مدخل برج النور (إياب)"),
    "FURNA-RETOUR": ("Furna (Retour)", "فورنة (إياب)"),
    "MESSAADINE-RETOUR": ("Messaadine (Retour)", "المساعدين (إياب)"),
    "KM30-RETOUR": ("Km 30 (Retour)", "الكيلومتر 30 (إياب)"),
    "KIOSQUE AGIL -RETOUR": ("Kiosque Agil (Retour)", "محطة عجيل (إياب)"),
    "FRINECH": ("Frinech", "فرينش"),
    "ROUTE SIDI MEDIEN-ALLER": ("Route Sidi Medien (Aller)", "طريق سيدي مدين (ذهاب)"),
    "SIDI MEDIEN": ("Sidi Medien", "سيدي مدين"),
    "ROUTE SIDI MEDIEN-RETOUR": ("Route Sidi Medien (Retour)", "طريق سيدي مدين (إياب)"),
    "RABATTEMENT MOUROUJ 2": ("Rabattement Mourouj 2", "محطة المروج 2"),
    "GARDE NATIONAL FOUCHANA": ("Garde Nationale Fouchana", "الحرس الوطني فوشانة"),
    "LYCÉE FOUCHANA": ("Lycée Fouchana", "معهد فوشانة"),
    "FERME GAMMOUDI": ("Ferme Gammoudi", "ضيعة القمودي"),
    "HUILERIE BEN SAIDAINE": ("Huilerie Ben Saïdane", "معصرة بن سعيدان"),
    "CITÉ EL OUIFAK 2": ("Cité El Ouifak 2", "حي الوفاق 2"),
    "ENKHILETTE": ("Enkhilette", "النخيلات"),
    "LYCÉE SIDI AMOR": ("Lycée Sidi Amor", "معهد سيدي عمر"),
    "BUREAU DE POSTE RAOUED": ("Bureau de Poste Raoued", "مكتب بريد رواد"),
    "CAFÉ MANACHOU": ("Café Manachou", "مقهى مناشو"),
    "LYCÉE RAOUED": ("Lycée Raoued", "معهد رواد"),
    "TERMINUS RAOUED": ("Terminus Raoued", "نهاية الخط رواد"),
    "CHORFECH 3": ("Chorfech 3", "شرفش 3"),
    "CANAL CHORFECH": ("Canal Chorfech", "قنال شرفش"),
    "OUED ELMELAH": ("Oued El Melah", "وادي المالح"),
    "ARRÉT EL KAABI": ("Arrêt El Kaabi", "موقف الكعبي"),
    "TERMINUS 31": ("Terminus 31", "نهاية الخط 31"),
    "PONT BIZERTE GLASSE RETOUR": ("Pont Bizerte Glasse (Retour)", "جسر بنزرت غلاس (إياب)"),
    "PONT BIZERTE 2": ("Pont Bizerte 2", "جسر بنزرت 2"),
    "FERME BZAZEYA": ("Ferme Bzazeya", "ضيعة البزازية"),
    "DAR AMMAR": ("Dar Ammar", "دار عمار"),
    "HADJ HMEYDI": ("Hadj Hmeydi", "الحاج حميدي"),
    "TERMINUS BECH HAMBA": ("Terminus Béch Hamba", "نهاية الخط بش حامبة"),
    "PONT BIZERTE GLASSE": ("Pont Bizerte Glasse", "جسر بنزرت غلاس"),
    "PONT BIZERTE": ("Pont Bizerte", "جسر بنزرت"),
    "TOBYAS": ("Tobyas", "توبياس"),
    "METHALI": ("Methali", "المثالي"),
    "OUED MAJERDA": ("Oued Majerda", "وادي مجردة"),
    "GESSIR 1": ("Gessir 1", "القصير 1"),
    "GESSIR 2": ("Gessir 2", "القصير 2"),
    "HUILERIE ENTRÉE GALAAT": ("Huilerie Entrée Galaat", "معصرة مدخل قلعة الأندلس"),
    "RÉSERVOIR D'EAU": ("Réservoir d'Eau", "خزان الماء"),
    "EJJBAL": ("Ejjbal", "الجبال"),
    "EL FAJJA": ("El Fajja", "الفرجة"),
    "EJJBAL 2": ("Ejjbal 2", "الجبال 2"),
    "EJJBAL 3": ("Ejjbal 3", "الجبال 3"),
    "MUNICIPALE": ("Municipale", "البلدية"),
    "BEN NICHA": ("Ben Nicha", "بن نيشة"),
    "KAMBOUZA": ("Kambouza", "قمبوزة"),
    "ERRMILA": ("Errmila", "الرميلة"),
    "ROUTE LYCÉE": ("Route du Lycée", "طريق المعهد"),
    "LYCÉE KALAATE AL ANDALOUSS": ("Lycée Kalaat El Andalous", "معهد قلعة الأندلس"),
    "LES ABATTOIRS": ("Les Abattoirs", "المسلخ البلدي"),
    "BEN DAHA-ALLER": ("Ben Daha (Aller)", "بن دحة (ذهاب)"),
    "TERMINUS 33B/32A/533": ("Terminus 33B/32A/533", "نهاية الخط 33B/32A/533"),
    "BIRINE-ALLER": ("Birine (Aller)", "بيرين (ذهاب)"),
    "BIRINE-RETOUR": ("Birine (Retour)", "بيرين (إياب)"),
    "GHDHAOUNIA MOSQUE-ALLER": ("Mosquée Ghdhaounia (Aller)", "جامع الغضاونية (ذهاب)"),
    "CROISEMENT ZAGHOUAN/FAJJA-ALLER": ("Croisement Zaghouan/Fajja (Aller)", "مفترق زغوان - الفرجة (ذهاب)"),
    "AIN ASKAR-ALLER": ("Aïn Askar (Aller)", "عين عسكر (ذهاب)"),
    "CROISEMENT AIN ASKAR-ALLER": ("Croisement Aïn Askar (Aller)", "مفترق عين عسكر (ذهاب)"),
    "FRACHICH-ALLER": ("Frachich (Aller)", "الفراشيش (ذهاب)"),
    "EL MNAGAA-ALLER": ("El Mnagaa (Aller)", "المنقعة (ذهاب)"),
    "FIRMA L34-ALLER": ("Ferme L34 (Aller)", "ضيعة ل34 (ذهاب)"),
    "EPICIER LAGRAA": ("Épicier Lagraa", "بقالة الأقرع"),
    "FIRMA L34-RETOUR": ("Ferme L34 (Retour)", "ضيعة ل34 (إياب)"),
    "EL MNAGAA-RETOUR": ("El Mnagaa (Retour)", "المنقعة (إياب)"),
    "FRACHICH-RETOUR": ("Frachich (Retour)", "الفراشيش (إياب)"),
    "CROISEMENT AIN ASKAR-RETOUR": ("Croisement Aïn Askar (Retour)", "مفترق عين عسكر (إياب)"),
    "AIN ASKAR-RETOUR": ("Aïn Askar (Retour)", "عين عسكر (إياب)"),
    "CROISEMENT ZAGHOUAN/FAJJA-RETOUR": ("Croisement Zaghouan/Fajja (Retour)", "مفترق زغوان - الفرجة (إياب)"),
    "GHDHAOUNIA MOSQUE-RETOUR": ("Mosquée Ghdhaounia (Retour)", "جامع الغضاونية (إياب)"),
    "INSTITUT NATIONAL DES SCIENCES APPLIQUÉES ET DE TECHNOLOGIE (I.N.S.A.T)": ("INSAT", "المعهد الوطني للعلوم التطبيقية والتكنولوجيا"),
    "TAHAR SFAR": ("Tahar Sfar", "طاهر صفر"),
    "CITÉ NEJIBA": ("Cité Nejiba", "حي نجيبة"),
    "MAASRA": ("Maasra", "المعصرة"),
    "EL HATHERMINE": ("El Hatharmine", "الهذارمين"),
    "CITÉ BEN GHENIA": ("Cité Ben Ghenia", "حي بن غنية"),
    "EL BATTAN": ("El Battan", "البطان"),
    "CITE ERRIMEL": ("Cité Errimel", "حي الرمال"),
    "PISCINE": ("Piscine", "المسبح البلدي"),
    "MOSQUÉE EL EL BATTAN": ("Mosquée El Battan", "جامع البطان"),
    "ESLAIAA": ("Eslaïaa", "السليعة"),
    "NUMÉRO 7": ("Numéro 7", "نمرة 7"),
    "BEN DHEFALLAH": ("Ben Dhefallah", "بن ضيف الله"),
    "ZOUITINA": ("Zouitina", "الزويتينة"),
    "ESSALAT": ("Essalat", "الصلات"),
    "ARRÉT USINE": ("Arrêt Usine", "موقف المعمل"),
    "BOUHNACHE1": ("Bouhnache 1", "بوحنش 1"),
    "BOUHNACHE2": ("Bouhnache 2", "بوحنش 2"),
    "BOUHNACHE3": ("Bouhnache 3", "بوحنش 3"),
    "TERMINUS 44/44A/77": ("Terminus 44/44A/77", "نهاية الخط 44/44A/77"),
    "CITÉ ERRAJET": ("Cité Errajet", "حي الرجاء"),
    "LYCÉE TECHNIQUE TEBOURBA": ("Lycée Technique Tébourba", "المعهد الفني بطبربة"),
    "HOPITAL TEBOURBA": ("Hôpital Tébourba", "مستشفى طبربة"),
    "FRIGO": ("Frigo", "مستودع التبريد"),
    "ROUTE CHOUIGUI": ("Route Chouigui", "طريق الشويقي"),
    "ENTREE CHOUIGUI": ("Entrée Chouigui", "مدخل الشويقي"),
    "TERMINUS CHOUIGUI": ("Terminus Chouigui", "نهاية الخط الشويقي"),
    "STEG TEBOURBA 45B": ("STEG Tébourba", "الستاغ طبربة"),
    "BIR ZITOUN": ("Bir Zitoun", "بئر زيتون"),
    "CITÉ ELBRAG": ("Cité El Brag", "حي البراق"),
    "CITÉ BOUSABAA": ("Cité Bousabaa", "حي بوسبع"),
    "GOMERYEN": ("Gomeryen", "القمريين"),
    "GOMERYEN 2": ("Gomeryen 2", "القمريين 2"),
    "SIDI SALEM": ("Sidi Salem", "سيدي سالم"),
    "CANAL": ("Canal", "القنال"),
    "MANZEL SHAL": ("Manzel Shal", "منزل الشعل"),
    "MAAFRINE": ("Maafrine", "المعافرين"),
    "LYCÉE TECHNIQUE L'ANGALINA": ("Lycée Technique L'Angalina", "المعهد التقني الأنجلينا"),
    "BORJE ETTOUTA": ("Borj Ettouta", "برج التوتة"),
    "SOCIÉTÉ DE FROMAGE": ("Société de Fromage", "شركة الأجبان"),
    "EZENGA": ("Ezenga", "الزنقة"),
    "ELAROUSSIA1": ("Elaroussia 1", "العروسية 1"),
    "AROUSSIA EL BARRAGE": ("Aroussia El Barrage", "العروسية السد"),
    "ELMOATMED": ("El Moatmed", "المعتمدية"),
    "ERRAYES": ("Errayes", "الرايس"),
    "TONGARE": ("Tongare", "تونغار"),
    "CITÉ ELBJAOUI": ("Cité El Bjaoui", "حي البجاوي"),
    "OUED EDHALEME": ("Oued Edhaleme", "وادي الظلام"),
    "PASSAGE TKAYA": ("Passage Tkaya", "ممر التكاية"),
    "ELMELASSINE": ("El Melassine", "الملاسين"),
    "BORJE ETTOUMI": ("Borj Ettoumi", "برج التومي"),
    "EL HAKIME": ("El Hakime", "الحكيم"),
    "EWLED BELAID": ("Ouled Belaïd", "أولاد بلعيد"),
    "DAR ELBIDHA": ("Dar El Bidha", "الدار البيضاء"),
    "EL HRACHNIA": ("El Hrachnia", "الحراشنية"),
    "LYCEE EL BATTAN": ("Lycée El Battan", "معهد البطان"),
    "CITÉ AKACHA": ("Cité Akacha", "حي عكاشة"),
    "PONT RACHED": ("Pont Rached", "جسر راشد"),
    "CITÉ ENNOUR": ("Cité Ennour", "حي النور"),
    "EL MEHRINE": ("El Mehrine", "المهرين"),
    "MAHFOURA": ("Mahfoura", "المحفورة"),
    "MAHFOURA 1": ("Mahfoura 1", "المحفورة 1"),
    "SICLOU": ("Siclou", "سيكلو"),
    "E.PRIMAIRE EL MAHFOURA": ("École Primaire El Mahfoura", "المدرسة الابتدائية المحفورة"),
    "BOUCHIBA": ("Bouchiba", "بوشيبة"),
    "TERMINUS LAAJEMA": ("Terminus Laajema", "نهاية الخط العجامة"),
    "FORET DE TEBOURBA": ("Forêt de Tébourba", "غابة طبربة"),
    "CROISEMENT MATEUR": ("Croisement Mateur", "مفترق ماطر"),
    "LYCÉE EDKHILA": ("Lycée Edkhila", "معهد الدخيلة"),
    "EDKHILA": ("Edkhila", "الدخيلة"),
    "TERMINUS EDKHILA": ("Terminus Edkhila", "نهاية الخط الدخيلة"),
    "E.P TEBOURBA": ("École Primaire Tébourba", "المدرسة الابتدائية بطبربة"),
    "LYCEE EDKHILA": ("Lycée Edkhila", "معهد الدخيلة"),
    "SIDI ABD ELBASSETTE": ("Sidi Abd El Basset", "سيدي عبد الباسط"),
    "AIN EZOMMITE": ("Aïn Ezommite", "عين الزميت"),
    "FERME EL HAJRI": ("Ferme El Hajri", "ضيعة الهجري"),
    "ELMELEHA": ("El Meleha", "الملاحة"),
    "EL BARRAGE": ("El Barrage", "السد"),
    "CITÉ EL AYARI": ("Cité El Ayari", "حي العياري"),
    "ECOLE EL HAWARIA": ("École El Hawaria", "مدرسة الهوارية"),
    "LANSARINE": ("Lansarine", "الأنصارين"),
    "RELAIS BORJ AMRI-ALLER": ("Relais Borj El Amri (Aller)", "استراحة برج العامري (ذهاب)"),
    "CITÉ AOUINE 5": ("Cité Aouine 5", "حي العوينة 5"),
    "CITÉ AOUINE 6": ("Cité Aouine 6", "حي العوينة 6"),
    "CITÉ AOUINE 7": ("Cité Aouine 7", "حي العوينة 7"),
    "RAISIN": ("Raisin", "العنب"),
    "DOKEN BEN TARCHA": ("Doken Ben Tarcha", "دكان بن طرشة"),
    "EL KALATOUS": ("El Kalatous", "الكلاتوس"),
    "CITÉ ELMHERINE": ("Cité El Mherine", "حي المهرين"),
}

# 2. Exact roadside dual carriageway pairs
# Form: (Northbound/Retour coords, Southbound/Aller coords)
ROADSIDE_PAIRS = {
    'TAOUFIK': {
        'southbound': (36.831696, 10.152933),
        'northbound': (36.832198, 10.154312)
    },
    'CAMPUS': {
        'southbound': (36.825369, 10.143889),
        'northbound': (36.825112, 10.143985)
    },
    '14 JANVIER': {
        'southbound': (36.823507, 10.141496),
        'northbound': (36.823507, 10.141813)
    },
    'SONED': {
        'southbound': (36.835594, 10.160092),
        'northbound': (36.836019, 10.161154)
    },
    'FOYER BARDO 2': {
        'southbound': (36.818324, 10.141459),
        'northbound': (36.818640, 10.141400)
    },
    'CAFÉ EL HAJ': {
        'southbound': (36.812835, 10.145171),
        'northbound': (36.812810, 10.144989)
    }
}

# Read staticTransit.js
with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

def clean_direction_tag(name):
    if not name: return ''
    n = re.sub(r'\s*[-–(]?\s*(ALLER|RETOUR|ذهاب|إياب|اياب|رجوع)\s*\)?$', '', name, flags=re.IGNORECASE).strip()
    return n

# Apply translations and roadside coordinates
stops_updated = 0
for l in lines:
    is_bus = l.get('type_id') == 'bus'
    lid = l['id']
    
    for dir_idx, gname, target_dir in [(0, 'stops_aller', 'aller'), (1, 'stops_retour', 'retour')]:
        stops = l.get(gname, [])
        for s in stops:
            s_name = s.get('name', '').strip()
            
            # Check 204 dictionary
            if s_name in TRANSLATIONS_204:
                fr_val, ar_val = TRANSLATIONS_204[s_name]
                s['name_fr'] = fr_val
                s['name_ar'] = ar_val
                stops_updated += 1
            
            # Check roadside carriageways for bus lines
            if is_bus:
                n_up = s_name.upper()
                for kw, coords_pair in ROADSIDE_PAIRS.items():
                    if kw in n_up:
                        # On lines heading South (Bardo/Omrane) Aller is Southbound, Retour is Northbound
                        # Special handling for line 36B and 38B
                        if lid in ['bus_846', 'bus_847', 'bus_848', 'bus_703', 'bus_772']:
                            if target_dir == 'aller':
                                s['lat'], s['lon'] = coords_pair['southbound']
                            else:
                                s['lat'], s['lon'] = coords_pair['northbound']

    # Update line directions and long names
    aller = l.get('stops_aller', [])
    retour = l.get('stops_retour', [])
    if aller:
        start_fr = clean_direction_tag(aller[0].get('name_fr', aller[0].get('name', '')))
        end_fr = clean_direction_tag(aller[-1].get('name_fr', aller[-1].get('name', '')))
        start_ar = clean_direction_tag(aller[0].get('name_ar', aller[0].get('name', '')))
        end_ar = clean_direction_tag(aller[-1].get('name_ar', aller[-1].get('name', '')))
        
        l['long_name_fr'] = f"{start_fr} - {end_fr}"
        l['long_name_ar'] = f"{start_ar} - {end_ar}"
        l['directions_fr'] = [f"Vers {end_fr}", f"Vers {start_fr}"]
        l['directions_ar'] = [f"إلى {end_ar}", f"إلى {start_ar}"]

print(f"Applied translations to {stops_updated} stop instances.")

# Write back
new_json_str = json.dumps(lines, ensure_ascii=False, indent=2)
new_content = content[:m.start(1)] + new_json_str + content[m.end(1):]

with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Saved updated src/data/staticTransit.js")
