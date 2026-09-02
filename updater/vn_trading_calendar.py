# -*- coding: utf-8 -*-
"""
vn_trading_calendar.py — LICH PHIEN GIAO DICH VIET NAM, dung chung cho cac bot TRADE.
=====================================================================================
BAN SAO SONG SINH — SUA MOT BAN PHAI CHEP SANG BAN KIA (cung quy uoc voi newsfeeds.py).
File nay + vn_holidays.json ton tai GIONG HET o hai repo tach roi:
    vn-bots/bot/vn_trading_calendar.py             (PrimeTrade + Moneyflow)
    finpath-personal/updater/vn_trading_calendar.py (Prime Finance: daily + intraday)
Hai repo chay tren hai GitHub Actions khac nhau, khong checkout cheo nhau duoc, nen
khong co cach nao import chung. Doi chieu bang dong VERSION ben duoi.
=====================================================================================
Vi sao co file nay: hai bot trade (utbot_discord_bot.py, momlowvol_discord_bot.py) chay
theo cron "T2-T6". Cron khong biet ngay le. Trong ky nghi le san dong cua nhung bot van
thuc day, van keo 60-180 ma qua vnstock, roi van dang len Discord mot bao cao Y HET bao
cao cua phien truoc — vi nen moi nhat van la phien cuoi cung truoc ky nghi. Nguoi dung
nhan thong bao trong ky nghi le va khong co cach nao phan biet no voi mot bao cao that.

CHU Y PHAM VI: file nay CHI danh cho bot TRADE. Bot vi mo va bot tin tuc (macro/) PHAI
tiep tuc chay 24/7 ke ca ngay le — thi truong the gioi, ty gia, tin tuc khong nghi Tet
theo Viet Nam, va do la yeu cau ro rang cua user (2026-08-31). Dung import file nay vao
macro/.

HAI LOP CHAN, CO Y DE DU THUA:
  Lop 1 — LICH (re, chan TRUOC khi fetch): should_run() tra False neu phien gan nhat da
    dong cua DA duoc bao cao roi. Tiet kiem ca ngan sach API cua lan chay do.
  Lop 2 — DU LIEU (chac, chan TRUOC khi gui): bot so ngay cua NEN MOI NHAT lay ve voi
    ngay da bao cao lan truoc. Bang nhau = khong co phien moi = khong gui gi.
Lop 2 moi la cai giet spam that su, va no KHONG phu thuoc vao do chinh xac cua lich.
Neu file lich thieu mot ngay nghi (nam moi chua cap nhat, nghi bat thuong do bao lu, san
tam ngung ky thuat), hau qua duy nhat la ton mot lan fetch vo ich — KHONG phai spam.
Do la ly do lop 1 duoc phep sai, con lop 2 thi khong.

NGUON LICH: bot/vn_holidays.json. Xem header "_meta" trong file do de biet ngay nao lay
tu dau va da xac minh the nao.
"""
import datetime as dt
import json
import os

VERSION = "2026-08-31"

HERE = os.path.dirname(os.path.abspath(__file__))
HOLIDAYS_PATH = os.path.join(HERE, "vn_holidays.json")

VN_TZ_OFFSET = 7        # gio Viet Nam = UTC+7

# Gio (VN) coi nhu phien HOM NAY da dong va du lieu EOD da san sang. ATC ket thuc 14:45,
# nguon du lieu chot so xong quanh 15:00-15:30. Hai bot deu duoc ban luc 16:05 nen nguong
# nay khong bao gio bi cham trong van hanh binh thuong; no chi quan trong khi ai do chay
# tay giua phien — luc do phien hom nay CHUA dong, va "phien gan nhat da dong" phai la
# HOM QUA, neu khong bot se bao cao mot cay nen chua chot.
SESSION_CLOSE_HOUR = 15


def vn_now():
    """Bay gio theo gio Viet Nam. KHONG dung datetime.now(): may ca nhan cua user chay
    UTC+9 con runner cua GitHub chay UTC — cung mot thoi diem cho ra hai ngay khac nhau,
    va lech mot ngay o day la lech ca mot phien giao dich."""
    return dt.datetime.now(dt.timezone.utc) + dt.timedelta(hours=VN_TZ_OFFSET)


_CACHE = {}


def load_holidays():
    """{ 'YYYY-MM-DD': 'ten ngay nghi' }. Thieu file -> rong (chi con quy tac cuoi tuan)."""
    if "h" not in _CACHE:
        days = {}
        meta = {}
        try:
            raw = json.load(open(HOLIDAYS_PATH, encoding="utf-8"))
            meta = raw.get("_meta", {})
            for year, items in raw.items():
                if year.startswith("_"):
                    continue
                for it in items:
                    days[it["date"]] = it.get("name", "nghỉ lễ")
        except FileNotFoundError:
            pass
        except Exception as e:
            # Lich hong KHONG duoc lam chet bot: lop 2 van chan spam duoc. Nhung phai on ao.
            print(f"[vn_trading_calendar] CANH BAO: khong doc duoc {HOLIDAYS_PATH}: "
                  f"{type(e).__name__}: {e}")
        _CACHE["h"] = days
        _CACHE["meta"] = meta
    return _CACHE["h"]


def covered_years():
    """Cac nam co du lieu trong file lich."""
    return sorted({d[:4] for d in load_holidays()})


def calendar_gap_warning(today=None):
    """Canh bao neu lich KHONG phu nam dang chay -> tra chuoi, hoac None neu on.

    Mot file lich het han khong bao loi: moi ngay thuong bong nhien thanh ngay giao dich,
    bot lai chay vao Tet nam sau. Lop 2 chan duoc spam nhung ngan sach API thi mat, va
    quan trong hon la KHONG AI BIET lich da cu. Ham nay de bot dan mot dong vao bao cao.
    """
    today = today or vn_now().date()
    yrs = covered_years()
    if not yrs:
        return "Chưa có file lịch nghỉ lễ (bot/vn_holidays.json) — cổng lịch đang tắt."
    if str(today.year) not in yrs:
        return (f"Lịch nghỉ lễ chưa có năm {today.year} (mới có {', '.join(yrs)}) — "
                f"cần cập nhật bot/vn_holidays.json.")
    # Con duoi 30 ngay la het nam ma nam sau chua co -> nhac truoc, dung doi den mung 1.
    if (dt.date(today.year, 12, 31) - today).days <= 30 and str(today.year + 1) not in yrs:
        return (f"Lịch nghỉ lễ chưa có năm {today.year + 1} — sắp hết năm, "
                f"cần cập nhật bot/vn_holidays.json.")
    return None


def holiday_name(d):
    """Ten ngay nghi le, hoac None neu khong phai ngay nghi (ke ca cuoi tuan)."""
    return load_holidays().get(d.isoformat())


def is_trading_day(d):
    """Ngay d co phai mot phien giao dich khong (T2-T6 va khong nam trong lich nghi)."""
    return d.weekday() < 5 and d.isoformat() not in load_holidays()


def prev_trading_day(d):
    """Phien giao dich gan nhat TRUOC ngay d."""
    x = d - dt.timedelta(days=1)
    for _ in range(30):          # 30 ngay du phu ky nghi Tet dai nhat
        if is_trading_day(x):
            return x
        x -= dt.timedelta(days=1)
    return x


def last_closed_session(now=None):
    """Phien gan nhat DA DONG CUA tinh den 'now' (gio VN).

    Hom nay la phien giao dich VA da qua SESSION_CLOSE_HOUR -> hom nay.
    Nguoc lai (cuoi tuan, ngay le, hoac dang trong phien) -> phien giao dich truoc do.
    """
    now = now or vn_now()
    today = now.date()
    if is_trading_day(today) and now.hour >= SESSION_CLOSE_HOUR:
        return today
    return prev_trading_day(today)


def should_run(last_reported_session, now=None):
    """Co nen chay lan nay khong. Tra (chay: bool, ly_do: str).

    'last_reported_session' = chuoi 'YYYY-MM-DD' cua phien MA BOT DA BAO CAO lan gan nhat
    (bot tu luu vao state cua no). None = chua tung bao cao -> luon chay.

    Chu y thiet ke: dieu kien KHONG phai "hom nay co phai ngay le khong" ma la "phien gan
    nhat da dong da duoc bao cao chua". Khac biet nay quan trong: neu lan chay thu Sau
    HONG (runner loi, workflow bi huy), thi thu Hai nghi le bot VAN chay va bao cao phien
    thu Sau con thieu — dung cai can lam. Quy tac "hom nay la ngay le thi nghi" se nuot
    luon bao cao do, ma tin hieu Ban cua UT Bot la su kien MOT NEN, khong phat lai.
    """
    now = now or vn_now()
    sess = last_closed_session(now)
    if last_reported_session and last_reported_session >= sess.isoformat():
        today = now.date()
        why = holiday_name(today) or ("cuối tuần" if today.weekday() >= 5 else
                                      "chưa đóng cửa phiên hôm nay" if today == sess or is_trading_day(today)
                                      else "không phải ngày giao dịch")
        return False, (f"Phiên gần nhất đã đóng cửa ({sess}) đã được báo cáo rồi "
                       f"— hôm nay {today} là {why}. Không có gì mới để gửi.")
    return True, f"Phiên gần nhất đã đóng cửa: {sess} (chưa báo cáo)."


if __name__ == "__main__":
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    # --gate: dung cho script .bat / shell. Ma thoat 0 = hom nay CO phien, 1 = ngay nghi.
    #   python vn_trading_calendar.py --gate || exit 0
    if "--gate" in sys.argv:
        d = vn_now().date()
        if is_trading_day(d):
            print(f"{d}: ngay giao dich -> chay tiep.")
            sys.exit(0)
        why = holiday_name(d) or "cuối tuần"
        print(f"{d}: KHONG phai ngay giao dich ({why}) -> bo qua.")
        sys.exit(1)

    now = vn_now()
    print(f"Bay gio (VN)          : {now:%Y-%m-%d %H:%M} ({now.strftime('%A')})")
    print(f"Nam co trong lich     : {', '.join(covered_years()) or '(khong co)'}")
    print(f"Hom nay la phien?     : {is_trading_day(now.date())}"
          + (f"  [{holiday_name(now.date())}]" if holiday_name(now.date()) else ""))
    print(f"Phien gan nhat da dong: {last_closed_session(now)}")
    w = calendar_gap_warning()
    if w:
        print(f"CANH BAO              : {w}")
    for lr in (None, last_closed_session(now).isoformat(), "2020-01-01"):
        run, why = should_run(lr, now)
        print(f"  da_bao_cao={str(lr):12s} -> chay={run}  ({why})")
