import random
from collections import Counter, defaultdict

import pandas as pd
import streamlit as st

from services.gas_client import simpan_jadwal, simpan_penugasan


HARI_URUT = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at", "Sabtu"]
JUMLAH_PERCOBAAN = 300


POLA_JP = {
    1: [[1]],
    2: [[2]],
    3: [[3], [2, 1]],
    4: [[2, 2]],
    5: [[3, 2]],
}

KOLOM = ["Nama Guru", "Mapel", "Kelas", "JP"]



def _norm_hari(hari):
    return "".join(ch for ch in str(hari).lower() if ch.isalpha())


def _norm_kelas(kelas):
    v = str(kelas).upper().replace(" ", "")
    for romawi, angka in (("VIII", "8"), ("VII", "7"), ("IX", "9")):
        if v.startswith(romawi):
            return angka + v[len(romawi):]
    return v


def _kode_str(value):
    try:
        return str(int(value))
    except (TypeError, ValueError):
        return str(value).strip()


def _opsi_blok(jp):

    if jp in POLA_JP:
        return POLA_JP[jp]

    depan, sisa = [], jp
    while sisa > 5:
        depan.append(3)
        sisa -= 3
    return [depan + p for p in POLA_JP[sisa]]


def _rentang(waktu):
 
    try:
        a, b = str(waktu).replace(":", ".").replace(" ", "").split("-")

        def menit(t):
            j, m = t.split(".")
            return int(j) * 60 + int(m)

        return menit(a), menit(b)
    except Exception:
        return None


def _kontinu(run):

    for x, y in zip(run, run[1:]):
        if y["jam_ke"] != x["jam_ke"] + 1:
            return False
        ra, rb = _rentang(x["waktu"]), _rentang(y["waktu"])
        if ra and rb and ra[1] != rb[0]:
            return False
    return True


def _slot_per_hari(data):

    slots = data["master"].get("slots", {}) or {}
    mentah = {}

    for nama, daftar in slots.items():
        urut = sorted(
            ({"jam_ke": int(s["jam_ke"]), "waktu": s["waktu"]} for s in daftar),
            key=lambda s: s["jam_ke"]
        )
        if urut:
            mentah[_norm_hari(nama)] = urut

    hasil = {}
    for h in HARI_URUT:
        if _norm_hari(h) in mentah:
            hasil[_norm_hari(h)] = (h, mentah[_norm_hari(h)])
    return hasil


def _keadaan_awal(jadwal):
    kelas_busy, guru_busy = set(), set()
    beban_guru, beban_kelas = defaultdict(int), defaultdict(int)

    for r in jadwal:
        try:
            jam = int(r.get("jam_ke"))
        except (TypeError, ValueError):
            continue
        hk = _norm_hari(r.get("hari", ""))
        kl = _norm_kelas(r.get("kelas", ""))
        kd = _kode_str(r.get("kode"))

        kelas_busy.add((hk, jam, kl))
        guru_busy.add((hk, jam, kd))
        beban_guru[(hk, kd)] += 1
        beban_kelas[(hk, kl)] += 1

    return kelas_busy, guru_busy, beban_guru, beban_kelas


def _sisa_tunggal(daftar, hk, kelas, kelas_busy, tambahan):

    bebas = [
        s["jam_ke"] not in tambahan and (hk, s["jam_ke"], kelas) not in kelas_busy
        for s in daftar
    ]
    n = 0
    for i, s in enumerate(daftar):
        if not bebas[i]:
            continue
        kiri = i > 0 and bebas[i - 1] and _kontinu([daftar[i - 1], s])
        kanan = (i + 1 < len(daftar) and bebas[i + 1]
                 and _kontinu([s, daftar[i + 1]]))
        if not (kiri or kanan):
            n += 1
    return n


def _tempatkan(t, slot_hari, keadaan, rng):
    kelas_busy, guru_busy, beban_guru, beban_kelas = keadaan
    kode, kelas = t["kode"], t["kelas_n"]

    for opsi in _opsi_blok(t["jp"]):
        hari_pakai, pilihan, ok = set(), [], True

        for n in sorted(opsi, reverse=True):
            kandidat = []

            for hk, (_, daftar) in slot_hari.items():
                if hk in hari_pakai:
                    continue
                for i in range(len(daftar) - n + 1):
                    run = daftar[i:i + n]
                    if not _kontinu(run):
                        continue
                    if any(
                        (hk, s["jam_ke"], kelas) in kelas_busy
                        or (hk, s["jam_ke"], kode) in guru_busy
                        for s in run
                    ):
                        continue
                   
                    skor = (
                        _sisa_tunggal(daftar, hk, kelas, kelas_busy,
                                      {s["jam_ke"] for s in run}),
                        beban_guru[(hk, kode)], beban_kelas[(hk, kelas)],
                    )
                    kandidat.append((skor, rng.random(), hk, run))

            if not kandidat:
                ok = False
                break

            _, _, hk, run = min(kandidat, key=lambda c: (c[0], c[1]))
            pilihan.append((hk, run))
            hari_pakai.add(hk)

        if ok:
            for hk, run in pilihan:
                for s in run:
                    kelas_busy.add((hk, s["jam_ke"], kelas))
                    guru_busy.add((hk, s["jam_ke"], kode))
                beban_guru[(hk, kode)] += len(run)
                beban_kelas[(hk, kelas)] += len(run)
            return opsi, pilihan

    return None


def _satu_percobaan(tugas, slot_hari, awal, rng, prioritas):
    keadaan = (
        set(awal[0]), set(awal[1]),
        defaultdict(int, awal[2]), defaultdict(int, awal[3]),
    )
   
    urutan = sorted(
        tugas,
        key=lambda t: (
            -prioritas[id(t)], -max(_opsi_blok(t["jp"])[0]), rng.random()
        )
    )

    berhasil, gagal = [], []
    for t in urutan:
        hasil = _tempatkan(t, slot_hari, keadaan, rng)
        if hasil is None:
            gagal.append(t)
        else:
            berhasil.append((t, hasil))

    return berhasil, gagal


def _auto_plot(tugas, slot_hari, jadwal_awal):
    awal = _keadaan_awal(jadwal_awal)
    rng = random.Random()

    prioritas = {id(t): 0 for t in tugas}

    terbaik = None
    for _ in range(JUMLAH_PERCOBAAN):
        berhasil, gagal = _satu_percobaan(tugas, slot_hari, awal, rng, prioritas)
        nilai = (len(gagal), sum(t["jp"] for t in gagal))
        for t in gagal:
            prioritas[id(t)] += 1

        if terbaik is None or nilai < terbaik[0]:
            terbaik = (nilai, berhasil, gagal)
        if not gagal:
            break

    _, berhasil, gagal = terbaik
    urut_hari = {hk: i for i, hk in enumerate(slot_hari)}

    rows, ringkasan = [], []

    for t, (opsi, pilihan) in berhasil:
        letak = []
        for hk, run in pilihan:
            nama_hari = slot_hari[hk][0]
            for s in run:
                rows.append({
                    "hari": nama_hari,
                    "waktu": s["waktu"],
                    "kelas": t["kelas"],
                    "nip": t["guru"]["nip"],
                    "guru": t["guru"]["nama"],
                    "mapel": t["mapel"],
                    "jam_ke": s["jam_ke"],
                    "kode": int(t["guru"]["kode"]),
                })
            jam = (
                f"{run[0]['jam_ke']}-{run[-1]['jam_ke']}"
                if len(run) > 1 else f"{run[0]['jam_ke']}"
            )
            letak.append(f"{nama_hari} jam {jam}")

        ringkasan.append({
            "Nama Guru": t["guru"]["nama"], "Mapel": t["mapel"],
            "Kelas": t["kelas"], "JP": t["jp"],
            "Pola": " + ".join(str(n) for n in opsi),
            "Penempatan": "; ".join(letak), "Status": "✓ Terplot",
        })

    for t in gagal:
        ringkasan.append({
            "Nama Guru": t["guru"]["nama"], "Mapel": t["mapel"],
            "Kelas": t["kelas"], "JP": t["jp"],
            "Pola": " + ".join(str(n) for n in _opsi_blok(t["jp"])[0]),
            "Penempatan": "-", "Status": "✗ Gagal (slot kosong tidak cukup)",
        })

    rows.sort(key=lambda r: (
        urut_hari[_norm_hari(r["hari"])], _norm_kelas(r["kelas"]), r["jam_ke"]
    ))

    return rows, pd.DataFrame(ringkasan), len(gagal)


def _cek_kapasitas(tugas, slot_hari):

    total_slot = sum(len(d) for _, d in slot_hari.values())
    per_kelas, per_guru, nama_kelas, nama_guru = defaultdict(int), defaultdict(int), {}, {}
    for t in tugas:
        per_kelas[t["kelas_n"]] += t["jp"]
        per_guru[t["kode"]] += t["jp"]
        nama_kelas[t["kelas_n"]] = t["kelas"]
        nama_guru[t["kode"]] = t["guru"]["nama"]

    pesan = []
    for k, jp in sorted(per_kelas.items()):
        if jp > total_slot:
            pesan.append(f"Kelas {nama_kelas[k]}: {jp} JP, padahal slot seminggu hanya {total_slot}.")
    for k, jp in per_guru.items():
        if jp > total_slot:
            pesan.append(f"{nama_guru[k]}: {jp} JP, padahal slot seminggu hanya {total_slot}.")
    return pesan, total_slot, per_kelas, nama_kelas


def _df_kosong():
    return pd.DataFrame(columns=KOLOM).astype({"JP": "int64"})


def _df_dari_db(data, guru_map, kelas_opsi):
    label_per_kode = {_kode_str(g.get("kode")): label for label, g in guru_map.items()}
    kelas_resmi = {_norm_kelas(k): k for k in kelas_opsi}

    baris, dilewati = [], 0
    for p in (data.get("master", {}).get("penugasan") or []):
        label = label_per_kode.get(_kode_str(p.get("kode")))
        try:
            jp = int(p.get("jp"))
        except (TypeError, ValueError):
            jp = 0
        if not label or jp <= 0:
            dilewati += 1
            continue
        kelas = str(p.get("kelas", ""))
        baris.append({
            "Nama Guru": label,
            "Mapel": str(p.get("mapel", "")),
            "Kelas": kelas_resmi.get(_norm_kelas(kelas), kelas),
            "JP": jp,
        })

    if not baris:
        return _df_kosong(), dilewati
    df = pd.DataFrame(baris, columns=KOLOM).astype({"JP": "int64"})
    return df, dilewati


def _simpan_tabel(df, guru_map):

    rows = []
    for _, r in df.iterrows():
        g = guru_map.get(r["Nama Guru"])
        if g is None:
            continue
        rows.append({
            "kode": int(g["kode"]),
            "mapel": str(r["Mapel"]),
            "kelas": str(r["Kelas"]),
            "jp": int(r["JP"]),
        })

    simpan_penugasan(rows)
    st.session_state.data.setdefault("master", {})["penugasan"] = rows


def _rapikan(df):

    return (
        df[KOLOM].dropna(subset=KOLOM)
        .astype({"JP": "int64"})
        .reset_index(drop=True)
    )


def _ganti_tabel(df_baru, guru_map, pesan):
    try:
        with st.spinner("Menyimpan penugasan..."):
            _simpan_tabel(df_baru, guru_map)
    except Exception as e:
        st.error(f"Gagal menyimpan penugasan ke server: {e}")
        return False

    st.session_state.pen_df = df_baru.reset_index(drop=True)
    st.session_state.penugasan_ver += 1
    st.session_state.pop("hasil_plot", None)
    st.session_state["_info_tambah"] = pesan
    st.rerun()



def penugasan_guru():
    data = st.session_state.data
    master = data.get("master", {})
    jadwal = data["jadwal"]

    slot_hari = _slot_per_hari(data)
    if not slot_hari:
        st.warning("Data slot jam pelajaran belum ada di database.")
        return

    guru_map = {
        f'{g.get("nama", "")} ({g.get("kode", "")})': g
        for g in data["guru"] if str(g.get("nama", "")).strip()
    }
    mapel_opsi = list((master.get("mapel_jp") or {}).keys()) or sorted(
        {str(r.get("mapel", "")) for r in jadwal if r.get("mapel")}
    )
    kelas_opsi = list(master.get("kelas") or sorted(
        {str(r.get("kelas", "")) for r in jadwal if r.get("kelas")}
    ))

    st.session_state.setdefault("penugasan_ver", 0)

    if (
        "pen_df" not in st.session_state
        or st.session_state.get("_pen_data_id") != id(data)
    ):
        df_db, dilewati = _df_dari_db(data, guru_map, kelas_opsi)
        st.session_state.pen_df = df_db
        st.session_state["_pen_data_id"] = id(data)
        st.session_state["_pen_dilewati"] = dilewati
        st.session_state.penugasan_ver += 1
        st.session_state.pop("hasil_plot", None)

    awal_df = st.session_state.pen_df

    # ---------- Input ----------
    with st.container(border=True, key="card_penugasan_input"):
        st.markdown("### Input Penugasan")
        st.caption(
            "Tabel ini berisi penugasan yang tersimpan di database (sama dengan "
            "yang dipakai bot). Tambah lewat form di bawah tabel; untuk menghapus, "
            "centang kolom Pilih lalu klik Hapus terpilih. Perubahan langsung "
            "disimpan. Aturan pecah JP: 5 = 3+2, 4 = 2+2, 3 = 3 (atau 2+1), 2 = 2."
        )

        if st.session_state.get("_pen_dilewati"):
            st.warning(
                f"{st.session_state['_pen_dilewati']} penugasan di database "
                "dilewati karena kode gurunya tidak ada di Data Guru atau JP "
                "tidak valid. Baris itu akan terhapus dari database saat tabel "
                "ini disimpan."
            )

        df_editor = awal_df.copy()
        df_editor.insert(0, "Pilih", False)

        editor = st.data_editor(
            df_editor,
            key=f"editor_penugasan_{st.session_state.penugasan_ver}",
            num_rows="fixed",
            use_container_width=True,
            hide_index=True,
            column_config={
                "Pilih": st.column_config.CheckboxColumn(
                    "Pilih", default=False, width="small"
                ),
                "Nama Guru": st.column_config.SelectboxColumn(
                    "Nama Guru", options=list(guru_map), required=True
                ),
                "Mapel": st.column_config.SelectboxColumn(
                    "Mapel", options=mapel_opsi, required=True
                ),
                "Kelas": st.column_config.SelectboxColumn(
                    "Kelas", options=kelas_opsi, required=True
                ),
                "JP": st.column_config.NumberColumn(
                    "JP", min_value=1, max_value=10, step=1, required=True
                ),
            },
        )

        sekarang = _rapikan(editor)
        ada_perubahan = (
            sekarang.to_dict("records")
            != awal_df.reset_index(drop=True).to_dict("records")
        )
        if ada_perubahan:
            st.warning("Ada perubahan di tabel yang belum disimpan ke database.")
            if st.button("💾 Simpan perubahan tabel", type="primary",
                         key="btn_simpan_tabel"):
                _ganti_tabel(sekarang, guru_map, "Perubahan tabel disimpan.")


        terpilih = editor["Pilih"].fillna(False).astype(bool)
        n_pilih = int(terpilih.sum())

        if st.button(
            f"Hapus terpilih ({n_pilih})",
            disabled=n_pilih == 0,
            key="btn_hapus_terpilih"
        ):
            sisa = _rapikan(editor.loc[~terpilih])
            _ganti_tabel(sisa, guru_map, f"{n_pilih} baris dihapus.")

     
        with st.expander(
            "➕ Tambah penugasan (bisa banyak kelas sekaligus)", expanded=True
        ):
            with st.form("form_tambah_penugasan", clear_on_submit=True):
                f1, f2 = st.columns(2)
                f_guru = f1.selectbox("Nama Guru", list(guru_map))
                f_mapel = f2.selectbox("Mapel", mapel_opsi)

                f3, f4 = st.columns([3, 1])
                f_kelas = f3.multiselect(
                    "Kelas (pilih satu atau lebih)", kelas_opsi
                )
                f_jp = f4.number_input(
                    "JP per kelas", min_value=1, max_value=10, value=2, step=1
                )

                tambah = st.form_submit_button("Tambah ke tabel", type="primary")

            if tambah:
                if not f_kelas:
                    st.error("Pilih minimal satu kelas.")
                else:
                    ada = {
                        (r["Nama Guru"], r["Mapel"], _norm_kelas(r["Kelas"]))
                        for _, r in sekarang.iterrows()
                    }
                    baru = [
                        {
                            "Nama Guru": f_guru, "Mapel": f_mapel,
                            "Kelas": k, "JP": int(f_jp),
                        }
                        for k in f_kelas
                        if (f_guru, f_mapel, _norm_kelas(k)) not in ada
                    ]
                    dilewati = len(f_kelas) - len(baru)

                    if baru:
                        gabung = _rapikan(pd.concat(
                            [sekarang, pd.DataFrame(baru, columns=KOLOM)],
                            ignore_index=True
                        ))
                        _ganti_tabel(
                            gabung, guru_map,
                            f"{len(baru)} baris ditambahkan"
                            + (
                                f", {dilewati} dilewati karena sudah ada."
                                if dilewati else "."
                            )
                        )
                    else:
                        st.warning("Semua kelas yang dipilih sudah ada di tabel.")

            if st.session_state.get("_info_tambah"):
                st.success(st.session_state.pop("_info_tambah"))

        # ---------- Baca isi tabel ----------
        tugas, tidak_lengkap = [], 0
        for _, r in editor.iterrows():
            if any(pd.isna(r[k]) for k in KOLOM):
                tidak_lengkap += 1
                continue
            g = guru_map.get(r["Nama Guru"])
            if g is None:
                tidak_lengkap += 1
                continue
            tugas.append({
                "guru": g,
                "kode": _kode_str(g["kode"]),
                "mapel": str(r["Mapel"]),
                "kelas": str(r["Kelas"]),
                "kelas_n": _norm_kelas(r["Kelas"]),
                "jp": int(r["JP"]),
            })

        if tidak_lengkap:
            st.warning(f"{tidak_lengkap} baris belum lengkap dan akan dilewati.")

        dobel = [
            f"{m} kelas {k}"
            for (k, m, _), n in Counter(
                (t["kelas_n"], t["mapel"], t["kode"]) for t in tugas
            ).items()
            if n > 1
        ]
        if dobel:
            st.warning("Penugasan ganda untuk: " + ", ".join(dobel))

        st.caption(
            "Auto Plot menyusun ulang seluruh jadwal dari semua penugasan di "
            "tabel. Saat diterapkan, jadwal lama diganti seluruhnya."
        )

        if tugas:
            pesan_kap, total_slot, per_kelas, nama_kelas = _cek_kapasitas(tugas, slot_hari)
            if pesan_kap:
                st.error(
                    "Penugasan berikut pasti tidak muat, kurangi JP-nya:\n\n"
                    + "\n".join(f"- {p}" for p in pesan_kap)
                )
            with st.expander("Cek beban JP per kelas"):
                st.dataframe(
                    pd.DataFrame([
                        {"Kelas": nama_kelas[k], "Total JP": jp,
                         "Slot tersedia": total_slot,
                         "Sisa": total_slot - jp}
                        for k, jp in sorted(per_kelas.items())
                    ]),
                    use_container_width=True, hide_index=True
                )

        b1, b2, _ = st.columns([1.3, 1, 3])

        if b1.button(
            "⚙️ Auto Plot", type="primary",
            use_container_width=True, disabled=not tugas
        ):
            with st.spinner("Menyusun jadwal..."):
                rows, ringkasan, n_gagal = _auto_plot(tugas, slot_hari, [])

            st.session_state["hasil_plot"] = {
                "rows": rows,
                "ringkasan": ringkasan,
                "gagal": n_gagal,
                "ukuran_awal": len(jadwal),
            }

        with b2.popover("Kosongkan tabel", use_container_width=True):
            st.caption(
                "Semua penugasan akan dihapus dari database. "
                "Jadwal yang sudah tersimpan tidak ikut terhapus."
            )
            if st.button("Ya, kosongkan", type="primary",
                         key="btn_kosongkan_tabel"):
                _ganti_tabel(_df_kosong(), guru_map, "Tabel penugasan dikosongkan.")

    # ---------- Hasil ----------
    hasil = st.session_state.get("hasil_plot")
    if not hasil:
        return

    with st.container(border=True, key="card_penugasan_hasil"):
        st.markdown("### Hasil Auto Plot")

        m = st.columns(3)
        m[0].metric("Jam terjadwal", f"{len(hasil['rows'])} JP")
        m[1].metric("Penugasan terplot", len(hasil["ringkasan"]) - hasil["gagal"])
        m[2].metric("Penugasan gagal", hasil["gagal"])

        if hasil["gagal"]:
            st.warning(
                "Ada penugasan yang tidak muat. Biasanya karena kelasnya "
                "hampir penuh (sisa slot kecil, cek 'Cek beban JP per kelas') "
                "atau guru yang sama mengajar banyak kelas sehingga jamnya "
                "bentrok. Klik Auto Plot lagi untuk mencoba susunan lain, "
                "atau kurangi JP / ubah pembagian kelasnya."
            )

        st.dataframe(hasil["ringkasan"], use_container_width=True, hide_index=True)

        with st.expander("Lihat semua baris jadwal yang akan dibuat"):
            st.dataframe(
                pd.DataFrame(hasil["rows"]),
                use_container_width=True, hide_index=True
            )

        a1, a2, _ = st.columns([1.3, 1, 3])

        if a1.button(
            "Terapkan ke Jadwal", type="primary",
            use_container_width=True, disabled=not hasil["rows"]
        ):
            if len(data["jadwal"]) != hasil["ukuran_awal"]:
                st.error("Jadwal berubah sejak plotting. Jalankan Auto Plot ulang.")
            else:
                baru = list(hasil["rows"])
                try:
                    with st.spinner("Menyimpan jadwal ke server..."):
                        simpan_jadwal(baru)
                except Exception as e:
                    st.error(f"Gagal menyimpan ke server: {e}")
                else:
                    data["jadwal"] = baru
                    st.session_state.pop("hasil_plot", None)
                    st.toast("Jadwal berhasil diterapkan.")
                    st.rerun()

        if a2.button("Buang hasil", use_container_width=True):
            st.session_state.pop("hasil_plot", None)
            st.rerun()