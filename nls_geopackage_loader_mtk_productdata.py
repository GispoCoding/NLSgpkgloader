#  Gispo Ltd., hereby disclaims all copyright interest in the program NLSgpkgloadert
#  Copyright (C) 2018-2020 Gispo Ltd (https://www.gispo.fi/).
#
#
#  This file is part of NLSgpkgloadert.
#
#  NLSgpkgloadert is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  NLSgpkgloadert is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with NLSgpkgloadert.  If not, see <https://www.gnu.org/licenses/>.

MTK_ALL_PRODUCTS_URL = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/feed/mtp/maastotietokanta/kaikki"
MTK_ALL_PRODUCTS_DOWNLOAD_URL = "https://tiedostopalvelu.maanmittauslaitos.fi/tp/tilauslataus/tuotteet/maastotietokanta/kaikki"
MTK_LAYERS_KEY_PREFIX = "MTK"
MTK_ALL_PRODUCTS_TITLE = "Maastotietokanta, kaikki kohteet"
MTK_PRODUCT_NAMES = [
    "YhteisetTyypit", "Aallonmurtaja", "AidanSymboli", "Aita", "Allas", "AluemerenUlkoraja",
    "AmpumaAlue", "Ankkuripaikka", "Autoliikennealue", "HarvaLouhikko", "Hautausmaa", "Hietikko",
    "Hylky", "HylynSyvyys", "IlmaradanKannatinpylvas", "Ilmarata", "Jyrkanne", "Kaatopaikka", "Kaislikko",
    "KallioAlue", "KallioSymboli", "Kalliohalkeama", "Kansallispuisto", "Karttasymboli", "Kellotapuli", "Kivi",
    "Kivikko", "Korkeuskayra", "KorkeuskayranKorkeusarvo", "Koski", "KunnanHallintokeskus", "KunnanHallintoraja",
    "Kunta", "Lahde", "Lahestymisvalo", "Lentokenttaalue", "Louhos", "Luiska", "Luonnonpuisto", "Luonnonsuojelualue",
    "MaaAineksenottoalue", "Maasto2kuvionReuna", "MaastokuvionReuna", "Maatalousmaa", "MaatuvaVesialue",
    "Masto", "MastonKorkeus", "Matalikko", "Meri", "MerkittavaLuontokohde", "MetsamaanKasvillisuus",
    "MetsamaanMuokkaus", "MetsanRaja", "Muistomerkki", "Muuntaja", "Muuntoasema", "Nakotorni", "Niitty",
    "Osoitepiste", "Paikannimi", "Pato", "Pelastuskoodipiste", "PistolaituriViiva", "Portti", "Puisto",
    "PutkijohdonSymboli", "Putkijohto", "Puu", "Puurivi", "RajavyohykkeenTakaraja", "Rakennelma", "Rakennus",
    "Rakennusreunaviiva", "Rautatie", "Rautatieliikennepaikka", "RautatienSymboli", "Retkeilyalue", "Sahkolinja",
    "SahkolinjanSymboli", "Savupiippu", "SavupiipunKorkeus", "Selite", "SisaistenAluevesienUlkoraja", "Soistuma",
    "Sulkuportti", "Suo", "SuojaAlue", "SuojaAlueenReunaviiva", "Suojametsa", "Suojanne", "SuojelualueenReunaviiva",
    "SuurjannitelinjanPylvas", "Syvyyskayra", "SyvyyskayranSyvyysarvo", "Syvyyspiste", "TaajaanRakennettuAlue",
    "TaajaanRakennetunAlueenReuna", "Taytemaa", "Tervahauta", "Tiesymboli", "Tienroteksti", "Tieviiva",
    "Tulentekopaikka", "TulvaAlue", "TunnelinAukko", "Turvalaite", "Tuulivoimala", "Uittolaite", "Uittoranni",
    "UlkoJaSisasaaristonRaja", "UrheiluJaVirkistysalue", "ValtakunnanRajapyykki", "Varastoalue", "Vedenottamo",
    "VedenpinnanKorkeusluku", "Vesiasteikko", "Vesikivi", "Vesikivikko", "Vesikulkuvayla",
    "VesikulkuvaylanKulkusuunta", "VesikulkuvaylanTeksti", "Vesikuoppa", "Vesitorni", "Viettoviiva", "Virtausnuoli",
    "VirtavesiKapea", "VirtavesiAlue", "Jarvi"
]

MTK_STYLED_LAYERS = {
    "Vesitorni": "01_Vesitorni",
    "Tuulivoimala": "02_Tuulivoimala",
    "Savupiippu": "03_Savupiippu",
    "Nakotorni": "04_Nakotorni",
    "Masto": "05_Masto",
    "Vesikuoppa": "06_Vesikuoppa",
    "Vedenottamo": "07_Vedenottamo",
    "Lahde": "08_Lahde",
    "TunnelinAukko": "09_TunnelinAukko",
    "Selite": "10_Selite",
    "MetsamaanKasvillisuus": "11_MetsamaanKasvillisuus",
    "Kivi": "12_Kivi",
    "Kaislikko": "13_Kaislikko",
    "HarvaLouhikko": "14_HarvaLouhikko",
    "Paikannimi": "15_Paikannimi",
    "Rakennelma": "16_Rakennelma",
    "Tieviiva": "17_Tieviiva",
    "Rautatie": "18_Rautatie",
    "Sahkolinja": "19_Sahkolinja",
    "Aita": "20_Aita",
    "Aallonmurtaja": "21_Aallonmurtaja",
    "PistolaituriViiva": "22_PistolaituriViiva",
    "Luiska": "23_Luiska",
    "Jyrkanne": "24_Jyrkanne",
    "VirtavesiKapea": "25_VirtavesiKapea",
    "KorkeuskayranKorkeusarvo": "26_KorkeuskayranKorkeusarvo",
    "Korkeuskayra": "27_Korkeuskayra",
    "AmpumaAlue": "28_AmpumaAlue",
    "SuojaAlue": "29_SuojaAlue",
    "Luonnonsuojelualue": "30_Luonnonsuojelualue",
    "Kansallispuisto": "31_Kansallispuisto",
    "Kunta": "32_Kunta",
    "TaajaanRakennettuAlue": "33_TaajaanRakennettuAlue",
    "Rakennus": "34_Rakennus",
    "Varastoalue": "35_Varastoalue",
    "Autoliikennealue": "36_Autoliikennealue",
    "Lentokenttaalue": "37_Lentokenttaalue",
    "UrheiluJaVirkistysalue": "38_UrheiluJaVirkistysalue",
    "Hautausmaa": "39_Hautausmaa",
    "MaaAineksenottoalue": "40_MaaAineksenottoalue",
    "Maatalousmaa": "41_Maatalousmaa",
    "Puisto": "42_Puisto",
    "Niitty": "43_Niitty",
    "TulvaAlue": "44_TulvaAlue",
    "MaatuvaVesialue": "45_MaatuvaVesialue",
    "Soistuma": "46_Soistuma",
    "Suo": "47_Suo",
    "Taytemaa": "48_Taytemaa",
    "Kivikko": "49_Kivikko",
    "KallioAlue": "50_KallioAlue",
    "Hietikko": "51_Hietikko",
    "Jarvi": "52_Jarvi",
    "Allas": "53_Allas",
    "VirtavesiAlue": "54_VirtavesiAlue",
    "Meri": "55_Meri"
}

MTK_PRESELECTED_PRODUCTS = list(MTK_STYLED_LAYERS.keys())