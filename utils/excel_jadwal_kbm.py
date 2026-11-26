

from datetime import date
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.properties import PageSetupProperties



KOP = [
    "PEMERINTAH KABUPATEN MAJALENGKA",
    "SMP NEGERI 1 DAWUAN",
    "Jalan Desa Salawana Kecamatan Dawuan Majalengka",
    "Email : smpnegerionedawuan@gmail.com, Kode Pos 45453.",
]

KEPALA_DEFAULT = {
    "nama": "THAMRIN, S.T.",
    "pangkat": "Pembina Tk.1",
    "nip": "197504302006041007",
}

HARI_PIKET = ["Senin", "Selasa", "Rabu", "Kamis", "Jum'at"]

BULAN = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]

ROMAWI = {"7": "VII", "8": "VIII", "9": "IX"}
KELAS_KOLOM = [f"{t}{h}" for t in ("7", "8", "9") for h in "ABCDE"]  


_ISTIRAHAT = ("b", "09.40-10.00", "ISTIRAHAT")
_ISTIRAHAT_2 = ("b", "12.00-12.30", "ISTIRAHAT 2 / SHOLAT DZUHUR BERSAMA")

_JP_SENIN_KAMIS = [
    ("jp", "07.40-08.20", 1), ("jp", "08.20-09.00", 2), ("jp", "09.00-09.40", 3),
    _ISTIRAHAT,
    ("jp", "10.00-10.40", 4), ("jp", "10.40-11.20", 5), ("jp", "11.20-12.00", 6),
    _ISTIRAHAT_2,
    ("jp", "12.30-13.10", 7), ("jp", "13.10-13.50", 8),
]

_JP_SELASA_RABU = [
    ("jp", "07.00-07.40", 1), ("jp", "07.40-08.20", 2),
    ("jp", "08.20-09.00", 3), ("jp", "09.00-09.40", 4),
    _ISTIRAHAT,
    ("jp", "10.00-10.40", 5), ("jp", "10.40-11.20", 6), ("jp", "11.20-12.00", 7),
    _ISTIRAHAT_2,
    ("jp", "12.30-13.10", 8), ("jp", "13.10-13.50", 9),
]

HARI_LAYOUT = [
    ("SENIN", "senin", [
        ("k", "06.30-07.00",
         "PEMERIKSAAN KEBERSIHAN KUKU , KERAPIHAN RAMBUT, KELENGKAPAN PAKAIAN"),
        ("k", "07.00-07.40", "UPACARA BENDERA"),
    ] + _JP_SENIN_KAMIS),
    ("SELASA", "selasa", [("k", "06.30-07.00", "SENAM CERIA")] + _JP_SELASA_RABU),
    ("RABU", "rabu", [("k", "06.30-07.00", "LITERASI")] + _JP_SELASA_RABU),
    ("KAMIS", "kamis", [
        ("k", "06.30-07.00", "SHOLAT DHUHA"),
        ("k", "07.00-07.40", "KULIAH DHUHA"),
    ] + _JP_SENIN_KAMIS),
    ("JUM'AT", "jumat", [
        ("k", "06.30-07.00", "GEBER"),
        ("k", "07.00-07.30", "GEBER"),
        ("jp", "07.30-08.10", 1), ("jp", "08.10-08.50", 2), ("jp", "08.50-09.30", 3),
        ("b", "09.30-09.50", "ISTIRAHAT"),
        ("jp", "09.50-10.30", 4), ("jp", "10.30-11.10", 5), ("jp", "11.10-11.50", 6),
        ("k", "11.50-12.30", "SHOLAT JUM'AT"),
    ]),
]


C_HARI, C_WAKTU, C_JAM = 1, 2, 3
C_KELAS0 = 4                 
C_KODE, C_NAMA, C_MENGAJAR = 20, 21, 22   
C_VII, C_VIII, C_IX, C_PD, C_TOTAL, C_WALI = 23, 24, 25, 26, 27, 28
LAST_COL = C_WALI


THIN = Side(style="thin", color="000000")
MED = Side(style="medium", color="000000")
BORDER = Border(left=THIN, right=THIN, top=THIN, bottom=THIN)
BORDER_MED_BAWAH = Border(left=THIN, right=THIN, top=THIN, bottom=MED)
ABU_HEADER = "EDEDED"
ABU_ISTIRAHAT = "D9D9D9"
ABU_JAM_KOSONG = "E7E7E7"



# FUNGSI BANTU
def _norm_kelas(kelas):
    v = str(kelas).upper().replace(" ", "")
    for romawi, angka in (("VIII", "8"), ("VII", "7"), ("IX", "9")):
        if v.startswith(romawi):
            return angka + v[len(romawi):]
    return v


def _norm_hari(hari):
    return "".join(ch for ch in str(hari).lower() if ch.isalpha())


def _kode(val):
    try:
        return str(int(val))
    except (TypeError, ValueError):
        return str(val).strip()


def _urut_kode(item):
    try:
        return (0, int(item.get("kode")))
    except (TypeError, ValueError):
        return (1, str(item.get("kode", "")))


def _sel(ws, r, c, v=None, *, b=False, i=False, sz=9, h="center", wrap=False,
         fill=None, rot=0, color="000000", border=BORDER):
    cell = ws.cell(row=r, column=c, value=v)
    cell.font = Font(name="Calibri", size=sz, bold=b, italic=i, color=color)
    cell.alignment = Alignment(
        horizontal=h, vertical="center", wrap_text=wrap, textRotation=rot
    )
    if fill:
        cell.fill = PatternFill("solid", start_color=fill, end_color=fill)
    if border:
        cell.border = border
    return cell


def _gabung(ws, r1, c1, r2, c2, v=None, **kw):
    for rr in range(r1, r2 + 1):
        for cc in range(c1, c2 + 1):
            _sel(ws, rr, cc, None, **kw)
    ws.cell(row=r1, column=c1).value = v
    if (r1, c1) != (r2, c2):
        ws.merge_cells(
            start_row=r1, start_column=c1, end_row=r2, end_column=c2
        )


def _logo(ws, path, anchor):
    if not path or not Path(path).exists():
        return
    try:
        from openpyxl.drawing.image import Image
        img = Image(str(path))
        img.width, img.height = 72, 72
        ws.add_image(img, anchor)
    except Exception:
        pass  


# FUNGSI UTAMA
def buat_excel_jadwal_kbm(
    jadwal,
    guru,
    piket=None,
    tahun_mulai=2026,
    semester="GANJIL",
    tanggal=None,
    kepala=None,
    logo_kiri=None,
    logo_kanan=None,
):
   
    kepala = {**KEPALA_DEFAULT, **(kepala or {})}
    tanggal = tanggal or date.today()
    piket = piket or {}


    sel = {}    
    beban = {}   

    for r in jadwal:
        kode = _kode(r.get("kode"))
        kelas = _norm_kelas(r.get("kelas", ""))
        try:
            jam = int(r.get("jam_ke"))
        except (TypeError, ValueError):
            continue

        sel.setdefault((_norm_hari(r.get("hari", "")), jam, kelas), []).append(kode)

        b = beban.setdefault(kode, {"7": 0, "8": 0, "9": 0, "mapel": {}})
        tingkat = kelas[:1]
        if tingkat in ROMAWI:
            b[tingkat] += 1
        b["mapel"].setdefault(str(r.get("mapel", "")), set()).add(tingkat)

    wb = Workbook()
    ws = wb.active
    ws.title = "Jadwal KBM"
    ws.sheet_view.showGridLines = False

   
    ws.column_dimensions["A"].width = 4.5
    ws.column_dimensions["B"].width = 11.5
    ws.column_dimensions["C"].width = 5
    for c in range(C_KELAS0, C_KELAS0 + 15):
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = 4.3
    ws.column_dimensions["S"].width = 2
    widths = {C_KODE: 5, C_NAMA: 33, C_MENGAJAR: 36, C_VII: 5.5, C_VIII: 5.5,
              C_IX: 5.5, C_PD: 5.5, C_TOTAL: 7, C_WALI: 9}
    for c, w in widths.items():
        ws.column_dimensions[ws.cell(row=1, column=c).column_letter].width = w

  
    ukuran_kop = [11, 16, 9, 9]
    tebal_kop = [True, True, False, False]
    for i, teks in enumerate(KOP, start=1):
        _gabung(ws, i, 1, i, LAST_COL, teks, b=tebal_kop[i - 1],
                sz=ukuran_kop[i - 1], border=None)
    ws.row_dimensions[2].height = 24

    _gabung(ws, 6, 1, 6, LAST_COL,
            f"JADWAL KBM TATAP MUKA SEMESTER {semester.upper()}",
            b=True, sz=11, border=None)
    _gabung(ws, 7, 1, 7, LAST_COL,
            f"TAHUN PELAJARAN {tahun_mulai} / {tahun_mulai + 1}",
            b=True, sz=11, border=None)

    _logo(ws, logo_kiri, "B1")
    _logo(ws, logo_kanan, "W1")

    kode_tahun = f"{str(tahun_mulai)[2:]}{str(tahun_mulai + 1)[2:]}"
    _sel(ws, 9, C_KODE, f"BEBAN KERJA GURU {kode_tahun}", b=True, sz=9,
         h="left", border=None)

    # ---------- Header tabel jadwal ----------
    H1, H2, MULAI = 10, 11, 12
    hdr = dict(b=True, fill=ABU_HEADER)

    _gabung(ws, H1, C_HARI, H2, C_HARI, "HARI", rot=90, sz=8, **hdr)
    _gabung(ws, H1, C_WAKTU, H2, C_WAKTU, "WAKTU", **hdr)
    _gabung(ws, H1, C_JAM, H2, C_JAM, "JAM KE", rot=90, sz=8, **hdr)

    for k, tingkat in enumerate(("VII", "VIII", "IX")):
        c0 = C_KELAS0 + k * 5
        _gabung(ws, H1, c0, H1, c0 + 4, f"KELAS {tingkat}", **hdr)
        for j, huruf in enumerate("ABCDE"):
            _sel(ws, H2, c0 + j, huruf, **hdr)

    # ---------- Header tabel beban kerja ----------
    _gabung(ws, H1, C_KODE, H2, C_KODE, "KODE", rot=90, sz=8, **hdr)
    _gabung(ws, H1, C_NAMA, H2, C_NAMA, "NAMA GURU / NIP", **hdr)
    _gabung(ws, H1, C_MENGAJAR, H2, C_MENGAJAR, "MENGAJAR / JABATAN", **hdr)
    _gabung(ws, H1, C_VII, H1, C_TOTAL, "JUMLAH JAM", **hdr)
    for c, teks in zip(range(C_VII, C_TOTAL + 1),
                       ["VII", "VIII", "IX", "PD", "TOTAL"]):
        _sel(ws, H2, c, teks, sz=8, **hdr)
    _gabung(ws, H1, C_WALI, H2, C_WALI, "WALI KELAS", **hdr)

    # ---------- Isi jadwal ----------
    r = MULAI
    for label_hari, kunci, slots in HARI_LAYOUT:
        r_awal = r

        for tipe, waktu, isi in slots:
            _sel(ws, r, C_WAKTU, waktu, i=True)

            if tipe == "jp":
                _sel(ws, r, C_JAM, isi, i=True)
                for n, kls in enumerate(KELAS_KOLOM):
                    kode_list = sel.get((kunci, isi, kls), [])
                    bentrok = len(kode_list) > 1
                    _sel(ws, r, C_KELAS0 + n,
                         "/".join(kode_list) if kode_list else None,
                         i=True, b=bentrok,
                         color="C00000" if bentrok else "000000")
            else:
                istirahat = tipe == "b"
                _sel(ws, r, C_JAM, None, fill=ABU_JAM_KOSONG)
                _gabung(ws, r, C_KELAS0, r, C_KELAS0 + 14, isi,
                        b=True, i=True, sz=8 if len(isi) > 40 else 9,
                        fill=ABU_ISTIRAHAT if istirahat else None)
            r += 1

        r_akhir = r - 1
        _gabung(ws, r_awal, C_HARI, r_akhir, C_HARI, label_hari,
                b=True, rot=90, sz=9)

      
        for c in range(C_HARI, C_KELAS0 + 15):
            ws.cell(row=r_akhir, column=c).border = BORDER_MED_BAWAH

    baris_jadwal_akhir = r - 1

 
    rg = MULAI
    sum_vii = sum_viii = sum_ix = 0

    for g in sorted(guru, key=_urut_kode):
        kode = _kode(g.get("kode"))
        b = beban.get(kode, {"7": 0, "8": 0, "9": 0, "mapel": {}})
        total = b["7"] + b["8"] + b["9"]
        sum_vii += b["7"]
        sum_viii += b["8"]
        sum_ix += b["9"]

        mengajar = ", ".join(
            f"{mapel} " + ", ".join(ROMAWI[t] for t in sorted(ts) if t in ROMAWI)
            for mapel, ts in b["mapel"].items()
        ).strip()

        _gabung(ws, rg, C_KODE, rg + 1, C_KODE, kode, b=True)
        _sel(ws, rg, C_NAMA, str(g.get("nama", "")), h="left", sz=9)
        _sel(ws, rg + 1, C_NAMA, f"NIP {g.get('nip', '')}", h="left", sz=8)
        _sel(ws, rg, C_MENGAJAR, mengajar, h="left", sz=8, wrap=True)
        _sel(ws, rg + 1, C_MENGAJAR, str(g.get("jabatan", "") or ""),
             h="left", sz=8)

        for c, val in ((C_VII, b["7"]), (C_VIII, b["8"]), (C_IX, b["9"])):
            _gabung(ws, rg, c, rg + 1, c, val or None)
        _gabung(ws, rg, C_PD, rg + 1, C_PD, None)
        _gabung(ws, rg, C_TOTAL, rg + 1, C_TOTAL, total or None, b=True)
        _gabung(ws, rg, C_WALI, rg + 1, C_WALI,
                str(g.get("wali_kelas", "") or ""), sz=8)
        rg += 2

    
    _gabung(ws, rg, C_KODE, rg, C_MENGAJAR, "JUMLAH", b=True, fill=ABU_HEADER)
    for c, val in ((C_VII, sum_vii), (C_VIII, sum_viii), (C_IX, sum_ix),
                   (C_PD, None), (C_TOTAL, sum_vii + sum_viii + sum_ix)):
        _sel(ws, rg, c, val, b=True, fill=ABU_HEADER)
    _sel(ws, rg, C_WALI, None, fill=ABU_HEADER)

    # ---------- Jadwal piket & tanda tangan ----------
    rp = max(rg, baris_jadwal_akhir) + 2

    _gabung(ws, rp, C_NAMA, rp, C_MENGAJAR, "Jadwal Piket", b=True,
            fill=ABU_HEADER)
    for k, hari in enumerate(HARI_PIKET, start=1):
        _sel(ws, rp + k, C_NAMA, hari, h="left")
        _sel(ws, rp + k, C_MENGAJAR, piket.get(hari, ""), h="left")

    ttd_col = C_VII
    baris_ttd = [
        (f"Dawuan, {tanggal.day} {BULAN[tanggal.month - 1]} {tanggal.year}", {}),
        ("Kepala SMPN 1 Dawuan", {}),
        ("", {}), ("", {}), ("", {}),
        (kepala["nama"], {"b": True}),
        (kepala["pangkat"], {}),
        (f"NIP {kepala['nip']}", {}),
    ]
    for k, (teks, gaya) in enumerate(baris_ttd):
        _gabung(ws, rp + k, ttd_col, rp + k, LAST_COL, teks,
                h="left", sz=9, border=None, **gaya)

  
    ws.page_setup.orientation = "portrait"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 1
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_options.horizontalCentered = True
    ws.page_margins.left = ws.page_margins.right = 0.3
    ws.page_margins.top = ws.page_margins.bottom = 0.3

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()
