import enum


class KullanimDurumu(str, enum.Enum):
    MULK_SAHIBI = "Mülk Sahibi"
    BOS = "Boş"
    KIRACILI = "Kiracılı"
    BELIRTILMEMIS = "Belirtilmemiş" 


class IsitmaTipi(str, enum.Enum):
    KOMBI = "Kombi"
    KLIMA = "Klima"
    MERKEZI = "Merkezi"
    MERKEZI_PAY_OLCER = "Merkezi (Pay Ölçer)"
    SOBA = "Soba"
    KAT_KALORIFERI = "Kat Kaloriferi"
    GUNES_ENERJISI = "Güneş Enerjisi"
    JEOTERMAL_ISITMA = "Jeotermal Isıtma"
    YERDEN_ISITMA = "Yerden Isıtma"
    DOGALGAZ_SOBASI = "Doğalgaz Sobası"
    FANCOIL_UNITESI = "Fancoil Ünitesi"
    VRV = "VRV"
    ISI_POMPASI = "Isı Pompası"
    SOMINE = "Şömine"
    ISITMA_YOK = "Isıtma Yok"
    BELIRTILMEMIS = "Belirtilmemiş"


class Cephe(str, enum.Enum):
    KUZEY = "Kuzey"
    GUNEY = "Güney"
    DOGU = "Doğu"
    BATI = "Batı"