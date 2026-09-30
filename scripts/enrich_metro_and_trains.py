import json, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open('src/data/staticTransit.js', 'r', encoding='utf-8') as f:
    content = f.read()

m = re.search(r'export const STATIC_LINES\s*=\s*(\[.*?\]);\s*\n', content, re.DOTALL)
lines = json.loads(m.group(1))

METRO_STATION_MAP = {
    'PLACE BARCELONE': ('Place Barcelone', 'ساحة برشلونة'),
    'PLACE BARCELONE SUD': ('Place Barcelone (Sud)', 'ساحة برشلونة (جنوب)'),
    'BAB ALIOUA': ('Bab Alioua', 'باب عليوة'),
    'MOHAMED MANACHOU': ('Mohamed Manachou', 'محمد مناشو'),
    '13 AOUT': ('13 Août', '13 أوت'),
    'MOHAMED ALI': ('Mohamed Ali', 'محمد علي'),
    'KABARIA': ('El Kabaria', 'الكبارية'),
    'IBN SINA': ('Ibn Sina', 'ابن سينا'),
    'CITE ENNOUR': ('Cité Ennour', 'حي النور'),
    'OUERDIA 6': ('El Ouardia 6', 'الوردية 6'),
    'ABOU EL KACEM ECHEBBI': ('Aboulkacem Echebbi', 'أبو القاسم الشابي'),
    'BEN AROUS': ('Ben Arous', 'بن عروس'),
    'PLACE DE LA REPUBLIQUE': ('Place de la République (Passage)', 'ساحة الجمهورية (الباساج)'),
    'NELSON MANDELA': ('Nelson Mandela', 'نيلسون مانديلا'),
    'MOHAMED V': ('Mohamed V', 'محمد الخامس'),
    'PALESTINE': ('Palestine', 'فلسطين'),
    'LES JARDINS': ('Les Jardins', 'الحدائق'),
    'CITE EL KHADHRA': ('Cité El Khadhra', 'حي الخضراء'),
    'LA JEUNESSE': ('La Jeunesse', 'الشباب'),
    'CITE SPORTIVE': ('Cité Sportive', 'الحي الرياضي'),
    '10 DECEMBRE 1948': ('10 Décembre 1948', '10 ديسمبر'),
    'CITE DES SCIENCES': ('Cité des Sciences', 'مدينة العلوم'),
    'INDEPENDANCE': ('Indépendance', 'الاستقلال'),
    'ARIANA': ('Ariana', 'أريانة'),
    'TUNIS MARINE': ('Tunis Marine', 'تونس البحرية'),
    'FARHAT HACHED': ('Farhat Hached', 'فرحات حشاد'),
    'BAB SAADOUN': ('Bab Saadoun', 'باب سعدون'),
    'MEFTAH SAADALLAH': ('Meftah Saadallah', 'مفتاح سعد الله'),
    'ROMMANA': ('Rommana', 'الرمانة'),
    'CAMPUS': ('Campus', 'المركب الجامعي'),
    '14 JANVIER 2011': ('14 Janvier 2011', '14 جانفي 2011'),
    'LES YASMINE': ('Les Jasmins', 'الياسمين'),
    'INTILAKA': ('Intilaka', 'الانطلاقة'),
    'IBN KHALDOUN': ('Ibn Khaldoun', 'ابن خلدون'),
    'BOUCHOUCHA': ('Bouchoucha', 'بوشوشة'),
    '20 MARS': ('20 Mars', '20 مارس'),
    'LE BARDO': ('Le Bardo', 'باردو'),
    'ESSAADA': ('Essâada', 'السعادة'),
    'KASR EL WARD': ('Ksar El Warda', 'قصر الورد'),
    'KHEIREDDINE': ('Kheireddine', 'خير الدين'),
    'DEN DEN': ('Den Den', 'الدندان'),
    'MANNOUBA': ('La Manouba', 'منوبة'),
    'SLIMANE KAHIA': ('Slimane Kahia', 'سليمان كاهية'),
    'MONFLEURY': ('Montfleury', 'مونفلوري'),
    'BAB KHADRA': ('Bab El Khadhra', 'باب الخضراء'),
    'BAB LAASSAL': ('Bab Laassal', 'باب العسل'),
    'BAB EL ASSAL': ('Bab Laassal', 'باب العسل'),
    'EL MOUROUJ 1': ('El Mourouj 1', 'المروج 1'),
    'EL MOUROUJ 2': ('El Mourouj 2', 'المروج 2'),
    'EL MOUROUJ 3': ('El Mourouj 3', 'المروج 3'),
    'EL MOUROUJ 4': ('El Mourouj 4', 'المروج 4'),
    'EL MOUROUJ 5': ('El Mourouj 5', 'المروج 5'),
    'TGM GOULETTE VIEILLE': ('La Goulette Vieille', 'حلق الوادي القديمة'),
    'TGM GOULETTE NEUVE': ('La Goulette Neuve', 'حلق الوادي الجديدة'),
    'TGM CARTHAGE BYRSA': ('Carthage Byrsa', 'قرطاج بيرصة'),
    'TGM CARTHAGE DERMECH': ('Carthage Dermech', 'قرطاج درمش'),
    'TGM CARTHAGE HANNIBAL': ('Carthage Hannibal', 'قرطاج حنبعل'),
    'TGM CARTHAGE PRESIDENCE': ('Carthage Présidence', 'قرطاج الرئاسة'),
    'TGM SIDI BOU SAID': ('Sidi Bou Saïd', 'سيدي بوسعيد'),
    'TGM SIDI DHAHER': ('Sidi Dhrif', 'سيدي الظريف'),
    'TGM LA MARSA PLAGE': ('La Marsa Plage', 'شاطئ المرسى'),
}

for line in lines:
    if line.get('type_id') in ['metro', 'train']:
        for g in ['stops', 'stops_aller', 'stops_retour']:
            for s in line.get(g, []):
                s_name = s.get('name', '').strip().upper()
                for key, (fr, ar) in METRO_STATION_MAP.items():
                    if key in s_name or s_name in key:
                        s['name_fr'] = fr
                        s['name_ar'] = ar
                        break
        
        # Line names
        aller = line.get('stops_aller', []) or line.get('stops', [])
        if aller:
            s_first = aller[0]
            s_last = aller[-1]
            first_ar = s_first.get('name_ar') or s_first.get('name')
            last_ar = s_last.get('name_ar') or s_last.get('name')
            first_fr = s_first.get('name_fr') or s_first.get('name')
            last_fr = s_last.get('name_fr') or s_last.get('name')
            line['long_name_ar'] = f"{first_ar} - {last_ar}"
            line['long_name_fr'] = f"{first_fr} - {last_fr}"
            line['directions_ar'] = [f"إلى {last_ar}", f"إلى {first_ar}"]
            line['directions_fr'] = [f"Vers {last_fr}", f"Vers {first_fr}"]

# Write back
new_json_str = json.dumps(lines, ensure_ascii=False, indent=2)
new_content = content[:m.start(1)] + new_json_str + content[m.end(1):]

with open('src/data/staticTransit.js', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Metro and train lines enriched bilingually!")
