import streamlit as st
import pandas as pd
from io import BytesIO
from utils.excel_jadwal_kbm import buat_excel_jadwal_kbm
from utils.filter_absensi import filter_absensi, urut_kelas



try:
    import plotly.express as px
    PLOTLY_OK = True
except ImportError:
    PLOTLY_OK = False


# PENGATURAN GRAFIK

STATUS_ABSENSI = ["Hadir", "Izin", "Sakit", "Alpa"]
WARNA_ABSENSI = {
    "Hadir": "#1F63DB",   
    "Izin": "#7FC0FF",    
    "Sakit": "#F5B942",   
    "Alpa": "#E5484D",    
}

TINGKAT = ["VII", "VIII", "IX"]
WARNA_TINGKAT = {
    "VII": "#5AAEFF",
    "VIII": "#1F63DB",
    "IX": "#0B2559",
}


def _rapikan_grafik(fig, tinggi=360):
    fig.update_layout(
        height=tinggi,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Manrope, sans-serif", size=12, color="#13294D"),
        margin=dict(l=10, r=10, t=10, b=10),
        legend=dict(
            title=None, orientation="h",
            yanchor="bottom", y=1.02, xanchor="left", x=0
        ),
        bargap=0.35,
    )
    fig.update_xaxes(gridcolor="#E3ECF8", title_font=dict(size=12))
    fig.update_yaxes(gridcolor="#E3ECF8", title_font=dict(size=12))
    return fig


def _kode_str(value):
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(value).strip()


def _tingkat(kelas):
    v = str(kelas).upper().replace(" ", "")


    if v.startswith("VIII") or v.startswith("8"):
        return "VIII"
    if v.startswith("VII") or v.startswith("7"):
        return "VII"
    if v.startswith("IX") or v.startswith("9"):
        return "IX"

    return "Lainnya"



def ringkasan_admin():
    data = st.session_state.data
    jadwal = data.get("jadwal", [])
    guru = data.get("guru", [])
    siswa = data.get("siswa", [])
    master = data.get("master", {})

    total_guru = len(guru)
    total_siswa = len(siswa)

   
    kelas_dari_jadwal = {
        str(r.get("kelas", "")).replace(" ", "").upper() for r in jadwal
    }
    mapel_dari_jadwal = {str(r.get("mapel", "")) for r in jadwal}

    total_kelas = len(master.get("kelas") or kelas_dari_jadwal)
    total_mapel = len(master.get("mapel_jp") or mapel_dari_jadwal)


    total_jp = len(jadwal)
    rata_jp = round(total_jp / total_guru, 1) if total_guru else 0

    baris1 = st.columns(3)
    baris1[0].metric("Total Guru", total_guru)
    baris1[1].metric("Total Siswa", total_siswa)
    baris1[2].metric("Total Kelas", total_kelas)

    baris2 = st.columns(3)
    baris2[0].metric("Total Mata Pelajaran", total_mapel)
    baris2[1].metric("Total Jam Mengajar / Minggu", f"{total_jp} JP")
    baris2[2].metric("Rata-rata Jam per Guru", f"{rata_jp} JP")




def grafik_absensi_per_kelas(df):
    data = (
        df.assign(Kelas=df["Kelas"].astype(str))
        .groupby(["Kelas", "Status Kehadiran"])
        .size()
        .reset_index(name="Jumlah")
    )

    urutan_kelas = sorted(data["Kelas"].unique().tolist())

    if PLOTLY_OK:
        fig = px.bar(
            data,
            x="Kelas",
            y="Jumlah",
            color="Status Kehadiran",
            color_discrete_map=WARNA_ABSENSI,
            category_orders={
                "Kelas": urutan_kelas,
                "Status Kehadiran": STATUS_ABSENSI,
            },
            barmode="stack",
        )

        tertinggi = data.groupby("Kelas")["Jumlah"].sum().max()
        if tertinggi <= 10:
            fig.update_yaxes(dtick=1)

        fig.update_traces(
            hovertemplate="Kelas %{x}<br>%{fullData.name}: %{y} siswa<extra></extra>"
        )
        st.plotly_chart(
            _rapikan_grafik(fig),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    else:
        tabel = (
            data.pivot(
                index="Kelas",
                columns="Status Kehadiran",
                values="Jumlah"
            )
            .reindex(columns=STATUS_ABSENSI)
            .fillna(0)
        )
        st.bar_chart(
            tabel,
            color=[WARNA_ABSENSI[s] for s in STATUS_ABSENSI]
        )




def _data_beban_guru():
    jadwal = st.session_state.data["jadwal"]
    guru_list = st.session_state.data["guru"]

    hitung = {}
    for r in jadwal:
        kunci = (_kode_str(r.get("kode")), _tingkat(r.get("kelas", "")))
        hitung[kunci] = hitung.get(kunci, 0) + 1

    baris = []
    for g in guru_list:
        kode = _kode_str(g.get("kode"))
        nama = str(g.get("nama", kode))

        for tingkat in TINGKAT:
            baris.append({
                "Guru": nama,
                "Tingkat": tingkat,
                "Jam": hitung.get((kode, tingkat), 0),
            })

    return pd.DataFrame(baris)


def grafik_beban_guru():
    
    df = _data_beban_guru()

    if df.empty:
        st.info("Belum ada data guru.")
        return


    urutan = (
        df.groupby("Guru")["Jam"].sum().sort_values().index.tolist()
    )

    if PLOTLY_OK:
        fig = px.bar(
            df,
            x="Jam",
            y="Guru",
            color="Tingkat",
            orientation="h",
            color_discrete_map=WARNA_TINGKAT,
            category_orders={"Guru": urutan, "Tingkat": TINGKAT},
            barmode="stack",
        )

        fig.update_xaxes(title="Jam mengajar per minggu (JP)")
        fig.update_yaxes(title=None)
        fig.update_traces(
            hovertemplate="%{y}<br>Kelas %{fullData.name}: %{x} JP<extra></extra>"
        )

        tinggi = max(300, 42 * len(urutan) + 90)
        st.plotly_chart(
            _rapikan_grafik(fig, tinggi),
            use_container_width=True,
            config={"displayModeBar": False}
        )

    else:
        tabel = (
            df.pivot(index="Guru", columns="Tingkat", values="Jam")
            .reindex(columns=TINGKAT)
            .fillna(0)
        )
        st.bar_chart(
            tabel,
            color=[WARNA_TINGKAT[t] for t in TINGKAT]
        )



def _norm_hari(hari):
    return "".join(ch for ch in str(hari).lower() if ch.isalpha())


def _norm_kelas(kelas):
    v = str(kelas).upper().replace(" ", "")
    for romawi, angka in (("VIII", "8"), ("VII", "7"), ("IX", "9")):
        if v.startswith(romawi):
            return angka + v[len(romawi):]
    return v


def _cek_bentrok(rows, hari, jam_ke, kelas, kode):

    pesan = []
    for r in rows:
        if _norm_hari(r.get("hari")) != _norm_hari(hari):
            continue
        try:
            if int(r.get("jam_ke")) != int(jam_ke):
                continue
        except (TypeError, ValueError):
            continue

        if _norm_kelas(r.get("kelas")) == _norm_kelas(kelas):
            pesan.append(
                f"Kelas {kelas} sudah ada pelajaran {r.get('mapel')} "
                f"({r.get('guru')}) pada {hari} jam ke-{jam_ke}."
            )
        if str(r.get("kode")) == str(kode):
            pesan.append(
                f"{r.get('guru')} sudah mengajar {r.get('mapel')} di kelas "
                f"{r.get('kelas')} pada {hari} jam ke-{jam_ke}."
            )
    return pesan

def manajemen_jadwal():

    st.caption(
        ""
        ""
    )

    rows = st.session_state.data["jadwal"]

    

    with st.container(border=True, key="card_daftar_jadwal"):

        st.markdown("### Daftar Jadwal")

        if not rows:
            st.info("Belum ada jadwal.")
        else:

            # ---------- FILTER: NAMA GURU DAN KELAS ----------
            guru_opsi = ["Semua"] + sorted(
                {str(r.get("guru", "")) for r in rows if r.get("guru")}
            )
            kelas_opsi = ["Semua"] + sorted(
                {str(r.get("kelas", "")) for r in rows if r.get("kelas")},
                key=urut_kelas
            )

            
            if st.session_state.get("filter_guru_manajemen", "Semua") not in guru_opsi:
                st.session_state["filter_guru_manajemen"] = "Semua"
            if st.session_state.get("filter_kelas_manajemen", "Semua") not in kelas_opsi:
                st.session_state["filter_kelas_manajemen"] = "Semua"

            f1, f2, f3 = st.columns([2, 1, 1])

            pilih_guru = f1.selectbox(
                "Filter nama guru",
                guru_opsi,
                key="filter_guru_manajemen"
            )
            pilih_kelas = f2.selectbox(
                "Filter kelas",
                kelas_opsi,
                key="filter_kelas_manajemen"
            )

            
            hasil = [
                (idx, row) for idx, row in enumerate(rows)
                if (pilih_guru == "Semua" or str(row.get("guru", "")) == pilih_guru)
                and (pilih_kelas == "Semua" or str(row.get("kelas", "")) == pilih_kelas)
            ]

          
            per_halaman = 10
            jumlah_halaman = max(1, -(-len(hasil) // per_halaman))

           
            tanda = (pilih_guru, pilih_kelas)
            if st.session_state.get("_tanda_filter_manajemen") != tanda:
                st.session_state["_tanda_filter_manajemen"] = tanda
                st.session_state["halaman_manajemen"] = 1

            if st.session_state.get("halaman_manajemen", 1) > jumlah_halaman:
                st.session_state["halaman_manajemen"] = jumlah_halaman

            halaman = f3.number_input(
                "Halaman",
                min_value=1,
                max_value=jumlah_halaman,
                step=1,
                key="halaman_manajemen"
            )

            awal = (int(halaman) - 1) * per_halaman
            tampil = hasil[awal:awal + per_halaman]

            st.caption(
                f"Menampilkan {len(tampil)} dari {len(hasil)} jadwal "
                f"(total {len(rows)} jadwal), halaman {int(halaman)} "
                f"dari {jumlah_halaman}."
            )

            if not hasil:
                st.info("Tidak ada jadwal yang cocok dengan filter.")
            else:

                # Header tabel
                header = st.columns(
                    [0.8, 1.1, 0.7, 1.4, 1.1, 1.1, 0.7, 0.6, 1.0],
                    gap="small"
                )

                headers = [
                    "Hari", "Waktu", "Kelas", "NIP",
                    "Guru", "Mapel", "Jam ke", "Kode", "Aksi"
                ]

                for col, title in zip(header, headers):
                    col.markdown(f"**{title}**")

                st.divider()

                
                for idx, row in tampil:

                    cols = st.columns(
                        [0.8, 1.1, 0.7, 1.4, 1.1, 1.1, 0.7, 0.6, 1.0],
                        gap="small"
                    )

                    # Kolom data jadwal
                    values = [
                        row.get("hari", "-"),
                        row.get("waktu", "-"),
                        row.get("kelas", "-"),
                        row.get("nip", "-"),
                        row.get("guru", "-"),
                        row.get("mapel", "-"),
                        row.get("jam_ke", "-"),
                        row.get("kode", "-")
                    ]

                    for col, value in zip(cols[:8], values):
                        col.write(value)

                    
                    if cols[8].button(
                        "🗑️ Hapus",
                        key=f"hapus_jadwal_{idx}",
                        help="Hapus jadwal pada baris ini",
                        use_container_width=True
                    ):

                        deleted = rows.pop(idx)

                        st.toast(
                            f"Jadwal {deleted['kelas']} - "
                            f"{deleted['mapel']} berhasil dihapus."
                        )

                        st.rerun()

                    st.divider()

   
    # TAMBAH JADWAL
    

        with st.expander("➕ Tambah baris jadwal (1 JP)", expanded=False):

            data = st.session_state.data
            slots = data["master"].get("slots", {})

            
            a, b, c = st.columns(3)

            hari = a.selectbox(
                "Hari",
                ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu"],
                key="tj_hari"
            )

            slot_hari = next(
                (v for k, v in slots.items() if _norm_hari(k) == _norm_hari(hari)),
                []
            )
            peta_waktu = {int(s["jam_ke"]): s["waktu"] for s in slot_hari}
            opsi_jam = sorted(peta_waktu)

            if not opsi_jam:
                st.warning(
                    f"Belum ada data slot untuk hari {hari} di sheet Slot "
                    "(atau data belum dimuat ulang)."
                )
                jam_ke = None
                waktu = ""
            else:
                jam_ke = b.selectbox(
                    "Jam ke",
                    opsi_jam,
                    key=f"tj_jam_{_norm_hari(hari)}"
                )
                waktu = peta_waktu[jam_ke]

           
            c.text_input(
                "Waktu (otomatis)",
                value=waktu,
                disabled=True,
                key=f"tj_waktu_{_norm_hari(hari)}_{jam_ke}"
            )

            kelas = st.selectbox("Kelas", data["master"]["kelas"], key="tj_kelas")

            guru = st.selectbox(
                "Guru",
                data["guru"],
                format_func=lambda x: f'{x["nama"]} ({x["kode"]})',
                key="tj_guru"
            )

            mapel = st.selectbox(
                "Mata pelajaran",
                list(data["master"]["mapel_jp"].keys()),
                key="tj_mapel"
            )

         
            bentrok = []
            if jam_ke is not None:
                bentrok = _cek_bentrok(
                    data["jadwal"], hari, jam_ke, kelas, guru["kode"]
                )

            if bentrok:
                st.error(
                    "⚠️ Jadwal bentrok:\n\n"
                    + "\n".join(f"- {p}" for p in bentrok)
                )

            if st.button(
                "Tambah Jadwal",
                type="primary",
                disabled=bool(bentrok) or jam_ke is None,
                key="tj_tambah"
            ):
                data["jadwal"].append({
                    "hari": hari,
                    "waktu": waktu,
                    "kelas": kelas,
                    "nip": guru["nip"],
                    "guru": guru["nama"],
                    "mapel": mapel,
                    "jam_ke": int(jam_ke),
                    "kode": int(guru["kode"])
                })
                st.toast("Jadwal berhasil ditambahkan.")
                st.rerun()




def monitoring_absensi():

    df = pd.DataFrame(st.session_state.data["absensi"])

    if df.empty:
        st.info("Belum ada data absensi.")
        return

    st.caption(
        ""
        ""
    )


    with st.container(border=True, key="card_grafik_absensi"):
        st.markdown("### Kehadiran per Kelas")
        grafik_absensi_per_kelas(df)

 
    df = filter_absensi(df, "filter_absensi_admin")

    if df.empty:
        st.info("Tidak ada data absensi yang cocok dengan filter.")
        return

    st.caption(f"Menampilkan {len(df)} catatan absensi.")

    cols = st.columns(4)

    for col, status in zip(cols, STATUS_ABSENSI):

        col.metric(
            status,
            int((df["Status Kehadiran"] == status).sum())
        )

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )





def export_jadwal(user=None, role="Admin"):

   
    rows = st.session_state.data["jadwal"]

 
    if role == "Guru" and user:

        rows = [
            r for r in rows
            if str(r["kode"]) == str(user["kode"])
        ]


    elif role == "Siswa" and user:

        rows = [
            r for r in rows
            if r["kelas"].replace(" ", "")
            == user["kelas"].replace(" ", "")
        ]

    df = pd.DataFrame(rows)

    if df.empty:
        st.info("Tidak ada jadwal untuk diekspor.")
        return

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df.to_excel(
            writer,
            index=False,
            sheet_name="Jadwal"
        )

    st.download_button(
        label="Unduh Excel",
        data=output.getvalue(),
        file_name="jadwal_smpn1_dawuan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )



def jadwal_pelajaran():

    st.caption(
        ""
    )

    ringkasan_admin()

   
    df_all = pd.DataFrame(
        st.session_state.data["jadwal"]
    )

    if df_all.empty:
        st.info("Belum ada jadwal pelajaran.")
        return

   
    with st.container(border=True, key="card_grafik_beban_guru"):
        st.markdown("### Beban Jam Mengajar per Guru")
        grafik_beban_guru()

  
    kelas_options = ["Semua"] + sorted(
        df_all["kelas"].dropna().unique().tolist()
    )

    selected = st.selectbox(
        "Filter kelas",
        kelas_options
    )

    df_display = df_all.copy()

    if selected != "Semua":

        df_display = df_display[
            df_display["kelas"] == selected
        ]


    st.dataframe(
        df_display[
            ["hari", "waktu", "kelas", "mapel", "guru", "jam_ke"]
        ],
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        df_all.to_excel(
            writer,
            index=False,
            sheet_name="Jadwal Pelajaran"
        )

    st.download_button(
        label="Unduh Seluruh Jadwal (Excel)",
        data=output.getvalue(),
        file_name="Jadwal_Pelajaran_SMPN_1_Dawuan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )

    excel_kbm = buat_excel_jadwal_kbm(
        jadwal=st.session_state.data["jadwal"],
        guru=st.session_state.data["guru"],
        tahun_mulai=2026,
        semester="GANJIL",
        logo_kiri="assets/logo_kiri.png",    
        logo_kanan="assets/logo_kanan.png",  
    )

    st.download_button(
        label="Unduh Seluruh Jadwal Sesuai Template (Excel)",
        data=excel_kbm,
        file_name="Jadwal_KBM_SMPN_1_Dawuan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )