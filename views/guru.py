import html
from datetime import date
from io import BytesIO

import pandas as pd
import streamlit as st

from utils.filter_absensi import filter_absensi


try:
    import plotly.express as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False




HARI_URUT = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu"]

STATUS_ABSENSI = ["Hadir", "Izin", "Sakit", "Alpa"]
WARNA_ABSENSI = {
    "Hadir": "#1F63DB",
    "Izin": "#7FC0FF",
    "Sakit": "#F5B942",
    "Alpa": "#E5484D",
}

BIRU = "#1F63DB"
NAVY = "#0B2559"



def _norm_hari(hari):
   
    return "".join(ch for ch in str(hari).lower() if ch.isalpha())


NAMA_HARI = {_norm_hari(h): h for h in HARI_URUT}


def _norm_kelas(kelas):
    value = str(kelas).upper().replace(" ", "")

  
    for romawi, angka in (("VIII", "8"), ("VII", "7"), ("IX", "9")):
        if value.startswith(romawi):
            return angka + value[len(romawi):]

    return value


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


def _rapikan_grafik(fig, tinggi=320):
   
    fig.update_layout(
        height=tinggi,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", size=12, color="#13294D"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            title=None, orientation="h",
            yanchor="bottom", y=-0.2, xanchor="center", x=0.5
        ),
        bargap=0.4,
    )
    fig.update_xaxes(gridcolor="#E3ECF8")
    fig.update_yaxes(gridcolor="#E3ECF8")
    return fig




def _kartu_ringkasan(rows):
    total_jp = len(rows)
    kelas = {_norm_kelas(r.get("kelas", "")) for r in rows}
    mapel = {str(r.get("mapel", "")).strip() for r in rows}
    hari = {_norm_hari(r.get("hari", "")) for r in rows}

    cols = st.columns(4)
    cols[0].metric("Total Jam Mengajar / Minggu", f"{total_jp} JP")
    cols[1].metric("Kelas yang Diajar", len(kelas))
    cols[2].metric("Mata Pelajaran", len(mapel))
    cols[3].metric("Hari Mengajar", f"{len(hari)} hari")




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
                    f"<div class='gj-kelas'>{html.escape(str(it.get('kelas', '')))}</div>"
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




def _distribusi_per_hari(rows):
    hitung = {h: 0 for h in HARI_URUT}

    for r in rows:
        nama = NAMA_HARI.get(_norm_hari(r.get("hari", "")))
        if nama:
            hitung[nama] += 1

    hari_list = _hari_tampil(rows)

    return pd.DataFrame({
        "Hari": hari_list,
        "Jam": [hitung[h] for h in hari_list],
    })


def _grafik_distribusi(rows):
    df = _distribusi_per_hari(rows)

    if PLOTLY_OK:
        tertinggi = int(df["Jam"].max())
        warna = [
            NAVY if (v == tertinggi and v > 0) else BIRU
            for v in df["Jam"]
        ]

        fig = px.bar(
            df, x="Hari", y="Jam", text="Jam",
            category_orders={"Hari": df["Hari"].tolist()},
        )
        fig.update_traces(
            marker_color=warna,
            textposition="outside",
            hovertemplate="%{x}: %{y} JP<extra></extra>",
        )
        fig.update_yaxes(title="Jam mengajar (JP)",
                         range=[0, tertinggi + 1.5], dtick=1 if tertinggi <= 10 else None)
        fig.update_xaxes(title=None)

        st.plotly_chart(
            _rapikan_grafik(fig),
            use_container_width=True,
            config={"displayModeBar": False},
        )
        st.caption("Batang navy menandai hari paling padat.")

    else:
        st.bar_chart(df.set_index("Hari")["Jam"], color=BIRU)



def _absensi_guru(df, rows, user):
   
    if df.empty or not user:
        return df

    kelas_set = {_norm_kelas(r.get("kelas", "")) for r in rows}
    mapel_set = {str(r.get("mapel", "")).strip().lower() for r in rows}

    per_kelas = df[
        df["Kelas"].astype(str).map(_norm_kelas).isin(kelas_set)
    ]

    per_mapel = per_kelas[
        per_kelas["Mata Pelajaran"].astype(str).str.strip().str.lower()
        .isin(mapel_set)
    ]

    
    return per_mapel if not per_mapel.empty else per_kelas




def _grafik_kehadiran(df_abs):
    if df_abs.empty:
        st.info("Belum ada data kehadiran untuk pilihan ini.")
        return

    hitung = pd.DataFrame({
        "Status": STATUS_ABSENSI,
        "Jumlah": [
            int((df_abs["Status Kehadiran"] == s).sum())
            for s in STATUS_ABSENSI
        ],
    })

    if PLOTLY_OK:
        data = hitung[hitung["Jumlah"] > 0]

        fig = px.pie(
            data, names="Status", values="Jumlah", hole=0.55,
            color="Status", color_discrete_map=WARNA_ABSENSI,
            category_orders={"Status": STATUS_ABSENSI},
        )
        fig.update_traces(
            textinfo="value+percent",
            sort=False,
            hovertemplate="%{label}: %{value} siswa<extra></extra>",
        )
        fig.add_annotation(
            text=f"<b>{int(hitung['Jumlah'].sum())}</b><br>catatan",
            x=0.5, y=0.5, showarrow=False, font=dict(size=14, color=NAVY),
        )

        st.plotly_chart(
            _rapikan_grafik(fig),
            use_container_width=True,
            config={"displayModeBar": False},
        )

    else:
        st.bar_chart(hitung.set_index("Status")["Jumlah"], color=BIRU)




def jadwal_mengajar(user=None):
  
    data = st.session_state.data
    rows = data["jadwal"]

    if user:
        rows = [r for r in rows if str(r["kode"]) == str(user["kode"])]
    else:
        st.caption("Tampilan seluruh jadwal mengajar (Admin baca saja).")

    df = pd.DataFrame(rows)

    if df.empty:
        st.info("Belum ada jadwal mengajar.")
    else:
        df_abs_semua = pd.DataFrame(data["absensi"])
        df_abs = _absensi_guru(df_abs_semua, rows, user)

        # ---------- 1. KPI ----------
        _kartu_ringkasan(rows)

        # ---------- 2. JADWAL MINGGUAN ----------
        with st.container(border=True, key="card_guru_mingguan"):
            st.markdown("### Jadwal Mingguan")
            _jadwal_mingguan(rows)

        # ---------- 3 & 4. DISTRIBUSI + KEHADIRAN ----------
        kiri, kanan = st.columns(2)

        with kiri:
            with st.container(border=True, key="card_guru_distribusi"):
                st.markdown("### Distribusi Jadwal Mingguan")
                _grafik_distribusi(rows)

        with kanan:
            with st.container(border=True, key="card_guru_kehadiran"):
                st.markdown("### Riwayat Kehadiran")

                # Filter per kelas
                kelas_map = {}
                for r in rows:
                    kelas_map.setdefault(
                        _norm_kelas(r.get("kelas", "")),
                        str(r.get("kelas", "")).strip()
                    )
                kelas_opsi = [kelas_map[k] for k in sorted(kelas_map)]

                pilih_kelas = st.selectbox(
                    "Filter kelas",
                    ["Semua"] + kelas_opsi,
                    key="filter_kelas_kehadiran_guru"
                )

                df_kehadiran = df_abs
                if pilih_kelas != "Semua" and not df_abs.empty:
                    df_kehadiran = df_abs[
                        df_abs["Kelas"].astype(str).map(_norm_kelas)
                        == _norm_kelas(pilih_kelas)
                    ]

                _grafik_kehadiran(df_kehadiran)

        # ---------- DETAIL JADWAL ----------
        with st.container(border=True, key="card_guru_detail"):
            st.markdown("### Detail Jadwal Mengajar")

            days = ["Semua"] + [
                d for d in HARI_URUT
                if d in df["hari"].unique()
            ]
            day = st.selectbox("Filter hari", days, key="filter_hari_jadwal_guru")

            df_display = df.copy()
            if day != "Semua":
                df_display = df_display[df_display["hari"] == day]

            kolom_tampil = ["hari", "waktu", "kelas", "guru", "mapel", "jam_ke", "kode"]
            kolom_tampil = [k for k in kolom_tampil if k in df_display.columns]

            st.dataframe(
                df_display[kolom_tampil],
                use_container_width=True,
                hide_index=True
            )

            st.metric("Total alokasi", f"{len(df_display)} JP")

            
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df_display[kolom_tampil].to_excel(
                    writer,
                    index=False,
                    sheet_name="Jadwal Mengajar"
                )

            nama_file = "jadwal_mengajar.xlsx"
            if user:
                nama_file = f"jadwal_mengajar_{str(user.get('kode', 'guru'))}.xlsx"

            st.download_button(
                label="Unduh Jadwal Mengajar (Excel)",
                data=output.getvalue(),
                file_name=nama_file,
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )

    st.divider()

   
    rekap_absensi(user)


def rekap_absensi(user=None):
    data = st.session_state.data
    df = pd.DataFrame(data["absensi"])

    st.markdown(
        '<div class="page-heading">'
        '<div class="page-heading-icon">✓</div>'
        '<div>'
        '<h1>Rekap Absensi</h1>'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if df.empty:
        st.info("Belum ada data absensi.")
        return

    if user:
        teacher_codes = {
            str(r["kode"])
            for r in data["jadwal"]
            if str(r.get("nip", "")).strip() == str(user.get("nip", "")).strip()
        }
        
        allowed_classes = {
            _norm_kelas(r["kelas"])
            for r in data["jadwal"]
            if str(r["kode"]) in teacher_codes
        }
        df = df[df["Kelas"].astype(str).map(_norm_kelas).isin(allowed_classes)]
        st.caption(f"Rekap absensi kelas yang diajar oleh {user['nama']}.")
    else:
        st.caption("Tampilan rekap absensi (Admin baca saja).")

    if df.empty:
        st.info("Belum ada rekap absensi untuk cakupan akun ini.")
        return

    df = filter_absensi(df, "filter_rekap_guru")

    if df.empty:
        st.info("Tidak ada data absensi yang cocok dengan filter.")
        return

    st.caption(f"Menampilkan {len(df)} catatan absensi.")

    cols = st.columns(4)
    for col, status in zip(cols, STATUS_ABSENSI):
        col.metric(status, int((df["Status Kehadiran"] == status).sum()))

    st.dataframe(df, use_container_width=True, hide_index=True)