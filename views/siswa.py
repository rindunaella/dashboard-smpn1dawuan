import html
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st




HARI_URUT = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu"]
STATUS_ABSENSI = ["Hadir", "Izin", "Sakit", "Alpa"]




def normalisasi_kelas(kelas):
   

    value = str(kelas).upper().replace(" ", "")
    mapping = [
        ("VIII", "8"),
        ("VII", "7"),
        ("IX", "9")
    ]

    for roman, number in mapping:
        if value.startswith(roman):
            return number + value[len(roman):]

    return value




def _norm_hari(hari):
    return "".join(ch for ch in str(hari).lower() if ch.isalpha())


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _hari_ini():
   
    idx = date.today().weekday()
    return HARI_URUT[idx] if idx < len(HARI_URUT) else None


def _hari_tampil(rows):
    
    ada_sabtu = any(_norm_hari(r.get("hari", "")) == "sabtu" for r in rows)
    return HARI_URUT if ada_sabtu else HARI_URUT[:5]




_CSS_GRID = (
    "<style>"
    ".gj-wrap{overflow-x:auto;}"
    ".gj-table{width:100%;min-width:640px;border-collapse:separate;"
    "border-spacing:6px;table-layout:fixed;}"
    ".gj-table th{background:#0B2559;color:#FFFFFF !important;"
    "border-radius:10px;padding:.5rem .4rem;font-size:.8rem;"
    "font-weight:800;text-align:center;}"
    ".gj-table th.gj-today{background:#1F63DB;}"
    ".gj-table th.gj-jam{width:56px;}"
    ".gj-table td{vertical-align:top;border-radius:10px;"
    "padding:.45rem .55rem;font-size:.75rem;text-align:center;"
    "background:#F3F7FE;color:#9BB0D0;}"
    ".gj-table td.gj-jam{width:56px;background:#E8F1FF;color:#0B2559;"
    "font-weight:800;vertical-align:middle;}"
    ".gj-table td.gj-isi{background:#E8F1FF;border:1px solid #BBD5FA;"
    "text-align:left;color:#0B2559;}"
    ".gj-mapel{font-weight:800;font-size:.78rem;color:#0B2559 !important;}"
    ".gj-kelas{font-weight:700;color:#1F63DB !important;}"
    ".gj-waktu{color:#5A6F94 !important;font-size:.68rem;}"
    ".gj-sep{height:1px;background:#BBD5FA;margin:.35rem 0;}"
    "</style>"
)


def _html_jadwal_mingguan(rows):
  
    hari_list = _hari_tampil(rows)

    peta = {}
    jam_max = 0

    for r in rows:
        jam = _to_int(r.get("jam_ke"))
        if jam is None:
            continue

        kunci = (_norm_hari(r.get("hari", "")), jam)
        peta.setdefault(kunci, []).append(r)
        jam_max = max(jam_max, jam)

    if jam_max == 0:
        return None

    hari_ini = _norm_hari(_hari_ini() or "")

    kepala = "<tr><th class='gj-jam'>Jam</th>"
    for h in hari_list:
        kelas_css = "gj-today" if _norm_hari(h) == hari_ini else ""
        kepala += f"<th class='{kelas_css}'>{html.escape(h)}</th>"
    kepala += "</tr>"

    isi_tabel = ""
    for jam in range(1, jam_max + 1):
        isi_tabel += f"<tr><td class='gj-jam'>{jam}</td>"

        for h in hari_list:
            items = peta.get((_norm_hari(h), jam), [])

            if items:
                
                bagian = [
                    f"<div class='gj-mapel'>{html.escape(str(it.get('mapel', '')))}</div>"
                    f"<div class='gj-kelas'>{html.escape(str(it.get('guru', '')))}</div>"
                    f"<div class='gj-waktu'>{html.escape(str(it.get('waktu', '')))}</div>"
                    for it in items
                ]
                isi_tabel += (
                    "<td class='gj-isi'>"
                    + "<div class='gj-sep'></div>".join(bagian)
                    + "</td>"
                )
            else:
                isi_tabel += "<td>–</td>"

        isi_tabel += "</tr>"

    return (
        _CSS_GRID
        + "<div class='gj-wrap'><table class='gj-table'>"
        + kepala + isi_tabel
        + "</table></div>"
    )


def _jadwal_mingguan(rows):
    kode_html = _html_jadwal_mingguan(rows)

    if not kode_html:
        st.info("Jam ke pada jadwal belum terisi dengan benar.")
        return

    st.markdown(kode_html, unsafe_allow_html=True)
    st.caption("Kolom hari ini ditandai biru terang.")





def _rekap_kehadiran(user):
    
    df = pd.DataFrame(st.session_state.data["absensi"])

    if df.empty:
        st.info("Belum ada data absensi.")
        return

    
    df = df[
        df["NISN"].astype(str).str.strip()
        == str(user.get("nisn", "")).strip()
    ]

    if df.empty:
        st.info("Belum ada catatan absensi untuk Anda.")
        return

  
    mapel_opsi = ["Semua"] + sorted(
        df["Mata Pelajaran"].dropna().astype(str).unique().tolist()
    )

 
    if st.session_state.get("filter_mapel_kehadiran_siswa", "Semua") not in mapel_opsi:
        st.session_state["filter_mapel_kehadiran_siswa"] = "Semua"

    pilih_mapel = st.selectbox(
        "Filter mata pelajaran",
        mapel_opsi,
        key="filter_mapel_kehadiran_siswa"
    )

    if pilih_mapel != "Semua":
        df = df[df["Mata Pelajaran"].astype(str) == pilih_mapel]

    cols = st.columns(4)
    for col, status in zip(cols, STATUS_ABSENSI):
        col.metric(status, int((df["Status Kehadiran"] == status).sum()))

    total = len(df)
    hadir = int((df["Status Kehadiran"] == "Hadir").sum())

    st.caption(
        f"Tingkat kehadiran {hadir / total * 100:.1f}% dari {total} sesi "
        f"pelajaran yang tercatat ({pilih_mapel}). Satu sesi = satu jam pelajaran."
    )

    with st.expander("Lihat riwayat absensi"):
        kolom = [
            "Tanggal", "Mata Pelajaran", "Jam Mulai",
            "Jam Selesai", "Status Kehadiran"
        ]
        kolom = [k for k in kolom if k in df.columns]

       
        riwayat = df.sort_values(
            ["Tanggal", "Jam Mulai"], ascending=[False, True]
        )

        st.dataframe(
            riwayat[kolom],
            use_container_width=True,
            hide_index=True
        )





def jadwal_pelajaran(user=None):

    
    rows = st.session_state.data["jadwal"]

  
    if user:
        kelas_siswa = normalisasi_kelas(user["kelas"])

        rows = [
            r for r in rows
            if normalisasi_kelas(r["kelas"]) == kelas_siswa
        ]

        st.caption(f"Jadwal pelajaran kelas {user['kelas']}")

    else:
        st.caption("Tampilan jadwal pelajaran seluruh kelas (Admin baca saja).")

   
    df_display = pd.DataFrame(rows)

    if df_display.empty:
        st.info("Belum ada jadwal pelajaran untuk kelas Anda.")
        return

   
    kolom_tampil = [
        "hari",
        "waktu",
        "kelas",
        "mapel",
        "guru",
        "jam_ke"
    ]

   
    if user:
        with st.container(border=True, key="card_siswa_mingguan"):
            st.markdown("### Jadwal Mingguan")
            _jadwal_mingguan(rows)

        with st.container(border=True, key="card_siswa_kehadiran"):
            st.markdown("### Rekap Kehadiran Saya")
            _rekap_kehadiran(user)

    with st.container(border=True, key="card_siswa_detail"):
        st.markdown("### Detail Jadwal Pelajaran")

        
        st.dataframe(
            df_display[kolom_tampil],
            use_container_width=True,
            hide_index=True
        )

        st.divider()

        output = BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df_display[kolom_tampil].to_excel(
                writer,
                index=False,
                sheet_name="Jadwal Pelajaran"
            )

        st.download_button(
            label="Unduh Jadwal Pelajaran (Excel)",
            data=output.getvalue(),
            file_name="Jadwal_Pelajaran_Kelas.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )