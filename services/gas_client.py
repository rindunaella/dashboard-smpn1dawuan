import requests
import streamlit as st


@st.cache_data(ttl=300, show_spinner="Mengambil data sekolah...")
def _fetch():
    r = requests.get(
        st.secrets["GAS_URL"],
        params={"action": "get_all", "key": st.secrets["GAS_KEY"]},
        timeout=90,
    )
    r.raise_for_status()
    try:
        j = r.json()
    except ValueError:
        raise RuntimeError(
            "Apps Script tidak mengembalikan JSON. Cek akses 'Anyone', "
            f"URL /exec, dan New version. Awal respons: {r.text[:200]}"
        )
    if not j.get("success"):
        raise RuntimeError(j.get("message", "Gagal mengambil data dari GAS"))
    return j["data"]

def get_data():
    d = _fetch()
    absensi = [
        {
            "Tanggal": a["tanggal"],
            "Kelas": a["kelas"],
            "Mata Pelajaran": a["mapel"],
            "Jam Mulai": a["jam_mulai"],
            "Jam Selesai": a["jam_selesai"],
            "NISN": a["nisn"],
            "Nama Siswa": a["nama_siswa"],
            "Status Kehadiran": a["status"],
        }
        for a in d["absensi"]
    ]
    return {
        "jadwal": d["jadwal"],
        "guru": d["guru"],
        "siswa": d["siswa"],
        "absensi": absensi,
        "master": d["master"],
    }