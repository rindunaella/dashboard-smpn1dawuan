

import streamlit as st


def urut_kelas(kelas):
   
    v = str(kelas).upper().replace(" ", "")

    if v.startswith("VIII") or v.startswith("8"):
        urutan = 1
    elif v.startswith("VII") or v.startswith("7"):
        urutan = 0
    elif v.startswith("IX") or v.startswith("9"):
        urutan = 2
    else:
        urutan = 3

    return (urutan, v)


def _pilihan_valid(key, opsi):
    
    if st.session_state.get(key, "Semua") not in opsi:
        st.session_state[key] = "Semua"


def filter_absensi(df, prefix):
    
    kelas_opsi = ["Semua"] + sorted(
        df["Kelas"].dropna().astype(str).unique().tolist(),
        key=urut_kelas
    )
    mapel_opsi = ["Semua"] + sorted(
        df["Mata Pelajaran"].dropna().astype(str).unique().tolist()
    )

    _pilihan_valid(f"{prefix}_kelas", kelas_opsi)
    _pilihan_valid(f"{prefix}_mapel", mapel_opsi)

    c1, c2, c3 = st.columns(3)

    kelas = c1.selectbox("Filter kelas", kelas_opsi, key=f"{prefix}_kelas")
    mapel = c2.selectbox("Filter mata pelajaran", mapel_opsi, key=f"{prefix}_mapel")
    nama = c3.text_input(
        "Cari nama siswa",
        placeholder="Ketik nama siswa",
        key=f"{prefix}_nama"
    )

    hasil = df

    if kelas != "Semua":
        hasil = hasil[hasil["Kelas"].astype(str) == kelas]

    if mapel != "Semua":
        hasil = hasil[hasil["Mata Pelajaran"].astype(str) == mapel]

    nama = nama.strip()
    if nama:
        hasil = hasil[
            hasil["Nama Siswa"].astype(str).str.contains(
                nama, case=False, regex=False, na=False
            )
        ]

    return hasil