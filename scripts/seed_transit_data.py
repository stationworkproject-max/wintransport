import json, urllib.request

with open('supabase_user_session.json', 'r') as f:
    session = json.load(f)

access_token = session['access_token']

headers = {
    'Authorization': f'Bearer {access_token}',
    'User-Agent': 'Mozilla/5.0',
    'Content-Type': 'application/json'
}

def execute_sql(sql):
    data = json.dumps({"query": sql}).encode('utf-8')
    req = urllib.request.Request(
        'https://api.supabase.com/v1/projects/rqwpafatgsyncvretjym/database/query',
        data=data,
        headers=headers
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())

print("Seeding Transit Types...")
execute_sql("""
INSERT INTO public.transit_types (id, name, icon, color) VALUES
('metro', 'Métro Léger', 'train-front', '#0071e3'),
('tgm', 'TGM Banlieue Nord', 'tram-front', '#0000FF'),
('rfr', 'RFR Banlieue Rapide', 'train-track', '#34C759'),
('train', 'Train SNCFT', 'train-freight-front', '#FF9500'),
('bus', 'Bus Transtu', 'bus-front', '#E30613')
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, icon = EXCLUDED.icon, color = EXCLUDED.color;
""")

print("Seeding Lines...")
execute_sql("""
INSERT INTO public.transit_lines (id, type_id, short_name, long_name, color, text_color, route_id) VALUES
-- Métro
('m1', 'metro', '1', 'Place de Barcelone - Ben Arous', '#84C8EB', '#000000', 50),
('m2', 'metro', '2', 'Place de la République - L''Ariana', '#489224', '#FFFFFF', 51),
('m3', 'metro', '3', 'Tunis Marine - Ibn Khaldoun', '#003399', '#FFFFFF', 52),
('m4', 'metro', '4', 'Place de Barcelone - Kheireddine', '#FFCF06', '#000000', 53),
('m5', 'metro', '5', 'Place de Barcelone - Cité Intilaka', '#E5442E', '#FFFFFF', 54),
('m6', 'metro', '6', 'Tunis Marine - El Mourouj 4', '#4F3E90', '#FFFFFF', 55),
-- TGM
('tgm', 'tgm', 'TGM', 'Tunis Marine - La Goulette - La Marsa', '#0000FF', '#FFFFFF', 56),
-- RFR
('rfr-a', 'rfr', 'Ligne A', 'Tunis Ville - Erriadh (Banlieue Sud)', '#A736A8', '#FFFFFF', 19),
('rfr-d', 'rfr', 'Ligne D', 'Tunis Ville - Gobaa (Manouba)', '#489224', '#FFFFFF', 46),
('rfr-e', 'rfr', 'Ligne E', 'Tunis Ville - Bougatfa (Sidi Hassine)', '#D32F2F', '#FFFFFF', 47),
-- Trains
('tr-sahel', 'train', 'M-Sahel', 'Sousse Bab Jdid - Monastir - Mahdia', '#407E15', '#FFFFFF', 1),
('tr-sfax', 'train', 'Train Sfax', 'Tunis Ville - Sousse - Sfax - Gabès', '#97533A', '#FFFFFF', 18),
('tr-bizerte', 'train', 'Train Bizerte', 'Tunis Ville - Mateur - Bizerte', '#000080', '#FFFFFF', 4),
('tr-ghardimaou', 'train', 'Train Nord-Ouest', 'Tunis Ville - Béja - Jendouba - Ghardimaou', '#FF0000', '#FFFFFF', 14),
('tr-nabeul', 'train', 'Train Nabeul', 'Bir Bourekba - Hammamet - Nabeul', '#00AD9E', '#FFFFFF', 45),
-- Bus Transtu
('b-28d', 'bus', '28D', 'Tunis Marine - Carrefour - La Marsa', '#E30613', '#FFFFFF', 8295),
('b-20', 'bus', '20', 'Place Barcelone - Ariana - Raoued', '#E30613', '#FFFFFF', 8164),
('b-35', 'bus', '35', 'Tunis Marine - Aéroport Carthage - Soukra', '#FFCF06', '#000000', 889),
('b-43', 'bus', '43', 'Place Barcelone - Hôpital Rabta', '#E30613', '#FFFFFF', 7404),
('b-17', 'bus', '17', 'Place Barcelone - Mégrine - Radès Bac', '#E30613', '#FFFFFF', 7320)
ON CONFLICT (id) DO UPDATE SET 
    type_id = EXCLUDED.type_id,
    short_name = EXCLUDED.short_name,
    long_name = EXCLUDED.long_name,
    color = EXCLUDED.color,
    text_color = EXCLUDED.text_color,
    route_id = EXCLUDED.route_id;
""")

print("Seeding Key Stations...")
execute_sql("""
INSERT INTO public.transit_stations (id, stop_id, name, lat, lon, route_type) VALUES
-- Metro 1
('st-500', 500, 'Place Barcelone Sud', 36.7961000, 10.1805500, 1),
('st-501', 501, 'Bab Alioua', 36.7858000, 10.1798100, 1),
('st-502', 502, 'Mohamed Manachou', 36.7821000, 10.1798400, 1),
('st-503', 503, '13 Août', 36.7750400, 10.1792000, 1),
('st-504', 504, 'Mohamed Ali', 36.7678800, 10.1838800, 1),
('st-505', 505, 'Kabaria', 36.7597800, 10.1905900, 1),
('st-506', 506, 'Ibn Sina', 36.7542800, 10.1939300, 1),
('st-507', 507, 'Ouerdia 6', 36.7542400, 10.1990600, 1),
('st-508', 508, 'Cité Ennour', 36.7515000, 10.2047300, 1),
('st-509', 509, 'Abou El Kacem Echebbi', 36.7524600, 10.2147400, 1),
('st-510', 510, 'Ben Arous', 36.7554000, 10.2189800, 1),

-- Metro 2
('st-511', 511, 'Place de la République (Passage)', 36.8064900, 10.1808100, 1),
('st-512', 512, 'Nelson Mandela', 36.8124800, 10.1833300, 1),
('st-513', 513, 'Mohamed V', 36.8156800, 10.1835700, 1),
('st-514', 514, 'Palestine', 36.8200100, 10.1820600, 1),
('st-515', 515, 'Les Jardins', 36.8234600, 10.1855600, 1),
('st-516', 516, 'Cité El Khadhra', 36.8292300, 10.1903700, 1),
('st-517', 517, 'La Jeunesse', 36.8332900, 10.1827700, 1),
('st-518', 518, 'Cité Sportive', 36.8385200, 10.1819600, 1),
('st-519', 519, '10 Décembre 1948', 36.8442800, 10.1840600, 1),
('st-520', 520, 'Cité des Sciences', 36.8469900, 10.1923700, 1),
('st-521', 521, 'Indépendance', 36.8544100, 10.1959100, 1),
('st-522', 522, 'Ariana', 36.8597900, 10.1974800, 1),

-- Metro 3, 4, 5 common
('st-523', 523, 'Tunis Marine', 36.8002000, 10.1928300, 1),
('st-524', 524, 'Farhat Hached', 36.7979000, 10.1862000, 1),
('st-525', 525, 'Place Barcelone Nord', 36.7965200, 10.1798200, 1),
('st-526', 526, 'Habib Thameur', 36.8013100, 10.1786400, 1),
('st-527', 527, 'Bab El Khadhra', 36.8103000, 10.1723900, 1),
('st-528', 528, 'Bab Laassal', 36.8133100, 10.1681700, 1),
('st-529', 529, 'Bab Saadoun', 36.8098600, 10.1621900, 1),
('st-530', 530, 'Meftah Saadallah', 36.8132000, 10.1562600, 1),
('st-531', 531, 'Rommana', 36.8236500, 10.1508500, 1),
('st-532', 532, 'Campus Universitaire El Manar', 36.8260500, 10.1438500, 1),
('st-535', 535, 'Ibn Khaldoun', 36.8308300, 10.1341100, 1),

-- Metro 4
('st-536', 536, 'Bouchoucha', 36.8095300, 10.1502600, 1),
('st-537', 537, '20 Mars', 36.8083500, 10.1423800, 1),
('st-538', 538, 'Bardo', 36.8072400, 10.1352300, 1),
('st-539', 539, 'Essaidia', 36.8054100, 10.1266400, 1),
('st-540', 540, 'Khaznadar', 36.8042100, 10.1217700, 1),
('st-541', 541, 'Artisanat', 36.8029300, 10.1160100, 1),
('st-542', 542, 'Denden', 36.8022100, 10.1107500, 1),
('st-543', 543, 'Manouba', 36.8021100, 10.1026900, 1),
('st-544', 544, 'Slimene Kehia', 36.8033400, 10.0990800, 1),
('st-545', 545, 'Moncef Bey', 36.8052800, 10.0906500, 1),
('st-546', 546, 'Aboubaker Errazi', 36.8073900, 10.0824700, 1),
('st-547', 547, 'Pôle Technologique', 36.8081100, 10.0805300, 1),
('st-548', 548, 'Ksar El Warda', 36.8092000, 10.0746100, 1),
('st-549', 549, 'Campus Manouba', 36.8139600, 10.0598100, 1),
('st-550', 550, 'Kheireddine', 36.8153300, 10.0567800, 1),

-- Metro 5
('st-551', 551, 'Ettahrir', 36.8291800, 10.1286200, 1),
('st-552', 552, 'El Omrane Supérieur', 36.8304900, 10.1241100, 1),
('st-553', 553, 'Ettadhamen', 36.8358400, 10.1175900, 1),
('st-554', 554, 'Cité El Intilaka', 36.8393500, 10.1169500, 1),

-- Metro 6
('st-555', 555, 'Taher El Haddad', 36.7606500, 10.1870100, 1),
('st-556', 556, 'El Ghazeli', 36.7546600, 10.1876500, 1),
('st-557', 557, 'Cité Municipale', 36.7484400, 10.1887300, 1),
('st-558', 558, 'Ennesri', 36.7451700, 10.1904900, 1),
('st-559', 559, 'El Montazah', 36.7429000, 10.1931900, 1),
('st-560', 560, 'El Mourouj 2', 36.7421800, 10.1977400, 1),
('st-561', 561, 'El Mourouj 1', 36.7385400, 10.2065700, 1),
('st-562', 562, 'Environnement', 36.7331000, 10.2103800, 1),
('st-563', 563, 'El Mourouj 3', 36.7287000, 10.2107300, 1),
('st-564', 564, 'Les Martyrs', 36.7236400, 10.2121000, 1),
('st-565', 565, 'El Mourouj 4', 36.7196500, 10.2163900, 1),

-- TGM
('st-566', 566, 'Tunis Marine Nord', 36.8006935, 10.1917429, 1),
('st-567', 567, 'Le Bac', 36.8141776, 10.2924504, 1),
('st-568', 568, 'La Goulette', 36.8180512, 10.3019396, 1),
('st-569', 569, 'Goulette Neuve', 36.8198449, 10.3056014, 1),
('st-570', 570, 'Goulette Casino', 36.8242005, 10.3087735, 1),
('st-571', 571, 'Khiareddine TGM', 36.8287832, 10.3115529, 1),
('st-572', 572, 'Aéroport TGM', 36.8319472, 10.3138745, 1),
('st-573', 573, 'Le Kram', 36.8361705, 10.3166057, 1),
('st-574', 574, 'Carthage Salambo', 36.8415416, 10.3191045, 1),
('st-575', 575, 'Carthage Byrsa', 36.8461259, 10.3218453, 1),
('st-576', 576, 'Carthage Dermech', 36.8501222, 10.3255807, 1),
('st-577', 577, 'Carthage Hannibal', 36.8540842, 10.3298647, 1),
('st-578', 578, 'Carthage Présidence', 36.8582845, 10.3340053, 1),
('st-579', 579, 'Carthage Amilcar', 36.8647614, 10.3371811, 1),
('st-580', 580, 'Sidi Bou Saïd', 36.8712616, 10.3392410, 1),
('st-581', 581, 'Sidi Dhrif', 36.8769300, 10.3367500, 1),
('st-582', 582, 'La Corniche', 36.8821900, 10.3327600, 1),
('st-583', 583, 'Marsa Plage', 36.8804000, 10.3268000, 1),

-- RFR A / SNCFT Banlieue Sud
('st-202', 202, 'Tunis Ville (Gare Centrale)', 36.7947693, 10.1803806, 0),
('st-88', 88, 'Djebel Jelloud', 36.7727251, 10.2082258, 0),
('st-41', 41, 'Mégrine Riadh', 36.7702743, 10.2229004, 0),
('st-40', 40, 'Mégrine', 36.7683270, 10.2339183, 0),
('st-39', 39, 'Sidi Rézig', 36.7673336, 10.2445454, 0),
('st-38', 38, 'Lycée Technique Radès', 36.7667869, 10.2608437, 0),
('st-37', 37, 'Radès', 36.7683604, 10.2697350, 0),
('st-36', 36, 'Radès Méliane', 36.7629769, 10.2842731, 0),
('st-35', 35, 'Ez-Zahra', 36.7468002, 10.3070495, 0),
('st-45', 45, 'Ezzahra Lycée', 36.7390405, 10.3179647, 0),
('st-34', 34, 'Bou Kornine', 36.7347949, 10.3239341, 0),
('st-33', 33, 'Hammam Lif', 36.7294393, 10.3342066, 0),
('st-32', 32, 'Arrêt du Stade', 36.7234436, 10.3482081, 0),
('st-31', 31, 'Tahar Sfar', 36.7175239, 10.3596743, 0),
('st-30', 30, 'Hammam Chatt', 36.7136003, 10.3694051, 0),
('st-29', 29, 'Bir El Bey', 36.7102497, 10.3786432, 0),
('st-132', 132, 'Borj Cédria', 36.7034822, 10.3974291, 0),
('st-133', 133, 'Erriadh', 36.6995040, 10.4148400, 0),

-- RFR D (Manouba)
('st-217', 217, 'Saïda Manoubia', 36.7870675, 10.1655399, 0),
('st-218', 218, 'Mellassine', 36.7964883, 10.1553505, 0),
('st-219', 219, 'Erraoudha', 36.8018747, 10.1478132, 0),
('st-220', 220, 'Le Bardo', 36.8075477, 10.1343723, 0),
('st-221', 221, 'El Bortal', 36.8115007, 10.1173367, 0),
('st-222', 222, 'Mannouba (Gare)', 36.8161297, 10.1011079, 0),
('st-223', 223, 'Cité des Orangers', 36.8184848, 10.0860288, 0),
('st-224', 224, 'Gobaa', 36.8200508, 10.0754979, 0),
('st-230', 230, 'Gobaa Ville', 36.8222878, 10.0601549, 0),

-- RFR E (Sidi Hassine)
('st-225', 225, 'Ennajah', 36.7933228, 10.1548445, 0),
('st-226', 226, 'Ettayaran-Ezzouhour 1', 36.7921247, 10.1383966, 0),
('st-227', 227, 'Ezzouhour 2', 36.7878362, 10.1275725, 0),
('st-228', 228, 'El Hraïria', 36.7840847, 10.1169321, 0),
('st-229', 229, 'Bougatfa-Sidi Hassine', 36.7802399, 10.1020439, 0)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, lat = EXCLUDED.lat, lon = EXCLUDED.lon;
""")

print("Linking Stations to Lines...")
execute_sql("""
DELETE FROM public.transit_line_stops;

-- Metro 1 Link
INSERT INTO public.transit_line_stops (line_id, station_id, stop_sequence, direction) VALUES
('m1', 'st-500', 1, 'Ben Arous'),
('m1', 'st-501', 2, 'Ben Arous'),
('m1', 'st-502', 3, 'Ben Arous'),
('m1', 'st-503', 4, 'Ben Arous'),
('m1', 'st-504', 5, 'Ben Arous'),
('m1', 'st-505', 6, 'Ben Arous'),
('m1', 'st-506', 7, 'Ben Arous'),
('m1', 'st-507', 8, 'Ben Arous'),
('m1', 'st-508', 9, 'Ben Arous'),
('m1', 'st-509', 10, 'Ben Arous'),
('m1', 'st-510', 11, 'Ben Arous'),

-- Metro 2 Link
('m2', 'st-511', 1, 'Ariana'),
('m2', 'st-512', 2, 'Ariana'),
('m2', 'st-513', 3, 'Ariana'),
('m2', 'st-514', 4, 'Ariana'),
('m2', 'st-515', 5, 'Ariana'),
('m2', 'st-516', 6, 'Ariana'),
('m2', 'st-517', 7, 'Ariana'),
('m2', 'st-518', 8, 'Ariana'),
('m2', 'st-519', 9, 'Ariana'),
('m2', 'st-520', 10, 'Ariana'),
('m2', 'st-521', 11, 'Ariana'),
('m2', 'st-522', 12, 'Ariana'),

-- Metro 4 Link
('m4', 'st-525', 1, 'Kheireddine'),
('m4', 'st-526', 2, 'Kheireddine'),
('m4', 'st-527', 3, 'Kheireddine'),
('m4', 'st-528', 4, 'Kheireddine'),
('m4', 'st-529', 5, 'Kheireddine'),
('m4', 'st-536', 6, 'Kheireddine'),
('m4', 'st-537', 7, 'Kheireddine'),
('m4', 'st-538', 8, 'Kheireddine'),
('m4', 'st-539', 9, 'Kheireddine'),
('m4', 'st-540', 10, 'Kheireddine'),
('m4', 'st-541', 11, 'Kheireddine'),
('m4', 'st-542', 12, 'Kheireddine'),
('m4', 'st-543', 13, 'Kheireddine'),
('m4', 'st-544', 14, 'Kheireddine'),
('m4', 'st-545', 15, 'Kheireddine'),
('m4', 'st-546', 16, 'Kheireddine'),
('m4', 'st-547', 17, 'Kheireddine'),
('m4', 'st-548', 18, 'Kheireddine'),
('m4', 'st-549', 19, 'Kheireddine'),
('m4', 'st-550', 20, 'Kheireddine'),

-- TGM Link
('tgm', 'st-566', 1, 'Marsa Plage'),
('tgm', 'st-567', 2, 'Marsa Plage'),
('tgm', 'st-568', 3, 'Marsa Plage'),
('tgm', 'st-569', 4, 'Marsa Plage'),
('tgm', 'st-570', 5, 'Marsa Plage'),
('tgm', 'st-571', 6, 'Marsa Plage'),
('tgm', 'st-572', 7, 'Marsa Plage'),
('tgm', 'st-573', 8, 'Marsa Plage'),
('tgm', 'st-574', 9, 'Marsa Plage'),
('tgm', 'st-575', 10, 'Marsa Plage'),
('tgm', 'st-576', 11, 'Marsa Plage'),
('tgm', 'st-577', 12, 'Marsa Plage'),
('tgm', 'st-578', 13, 'Marsa Plage'),
('tgm', 'st-579', 14, 'Marsa Plage'),
('tgm', 'st-580', 15, 'Marsa Plage'),
('tgm', 'st-581', 16, 'Marsa Plage'),
('tgm', 'st-582', 17, 'Marsa Plage'),
('tgm', 'st-583', 18, 'Marsa Plage'),

-- RFR A Link
('rfr-a', 'st-202', 1, 'Erriadh'),
('rfr-a', 'st-88', 2, 'Erriadh'),
('rfr-a', 'st-41', 3, 'Erriadh'),
('rfr-a', 'st-40', 4, 'Erriadh'),
('rfr-a', 'st-39', 5, 'Erriadh'),
('rfr-a', 'st-38', 6, 'Erriadh'),
('rfr-a', 'st-37', 7, 'Erriadh'),
('rfr-a', 'st-36', 8, 'Erriadh'),
('rfr-a', 'st-35', 9, 'Erriadh'),
('rfr-a', 'st-45', 10, 'Erriadh'),
('rfr-a', 'st-34', 11, 'Erriadh'),
('rfr-a', 'st-33', 12, 'Erriadh'),
('rfr-a', 'st-32', 13, 'Erriadh'),
('rfr-a', 'st-31', 14, 'Erriadh'),
('rfr-a', 'st-30', 15, 'Erriadh'),
('rfr-a', 'st-29', 16, 'Erriadh'),
('rfr-a', 'st-132', 17, 'Erriadh'),
('rfr-a', 'st-133', 18, 'Erriadh'),

-- RFR E Link
('rfr-e', 'st-202', 1, 'Bougatfa'),
('rfr-e', 'st-217', 2, 'Bougatfa'),
('rfr-e', 'st-225', 3, 'Bougatfa'),
('rfr-e', 'st-226', 4, 'Bougatfa'),
('rfr-e', 'st-227', 5, 'Bougatfa'),
('rfr-e', 'st-228', 6, 'Bougatfa'),
('rfr-e', 'st-229', 7, 'Bougatfa');
""")

print("Transit Data Seeding Complete!")
