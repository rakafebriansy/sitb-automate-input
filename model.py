from datetime import datetime, date, time, timedelta

@dataclass
class Skrining:
    tgl_skrining: date
    kegiatan_id: int
    kegiatan_lain: str
    metode_id: int
    tempat_skrining_id: int
    tempat_skrining_lain: str
    jenis_unit_pelaksana_id: int
    unit_pelaksana_id: int
    nama_peserta: str
    alamat_ktp: str
    provinsi_ktp_id: int
    kabupaten_ktp_id: int
    kecamatan_ktp_id: int
    kelurahan_ktp_id: int
    status_domisili_id: int
    alamat_domisili: str
    provinsi_domisili_id: int
    kabupaten_domisili_id: int
    kecamatan_domisili_id: int
    kelurahan_domisili_id: int
    warga_negara_id: int
    nik: str
    pekerjaan_id: int
    tgl_lahir: date
    umur_th: int
    umur_bl: int
    jenis_kelamin_id: int
    no_telp: str
    berat_badan: float
    tinggi_badan: float
    imt: float
    status_gizi_id: int
    riwayat_kontak_tb_id: int
    jenis_kontak_id: int
    nama_kasus_indeks: str
    nik_kasus_indeks: str
    jenis_kasus_indeks_id: int
    risiko_1_id: int
    risiko_1_tgl: date
    # dst. hingga semua field risiko, gejala, cxr, tst
    insert_by: str
    insert_at: datetime
    update_by: str
    update_at: datetime
